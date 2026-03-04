"""
call_bedrock handler

Sends drift context to Amazon Bedrock (Claude) for reasoning about:
- What changed and why it matters
- Whether the change is likely intentional or accidental
- What the correct Terraform remediation should be

Input:  Full pipeline state ($.normalized + $.enriched)
Output: dict written to $.remediation by the state machine
"""

import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_client = boto3.client("bedrock-runtime")

MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"
)
MAX_TOKENS = int(os.environ.get("BEDROCK_MAX_TOKENS", "2048"))


SYSTEM_PROMPT = """You are an SRE agent analyzing AWS infrastructure drift.
A resource has gone NON_COMPLIANT according to an AWS Config rule.

Given the drift event details, current resource configuration, and any
prior incident history, produce a structured analysis with:

1. SUMMARY: One-sentence description of what drifted and why it matters.
2. RISK_ASSESSMENT: Is this critical, high, medium, or low risk?
   Explain what could be exploited or broken.
3. LIKELY_CAUSE: Was this probably intentional (e.g., a developer debugging)
   or accidental (e.g., misconfigured automation)?
4. REMEDIATION: The specific change needed to bring the resource back
   into compliance.
5. TERRAFORM_SNIPPET: A valid Terraform resource block that enforces
   the compliant state. Use realistic resource names and include
   comments explaining each argument.

Respond in valid JSON with these five keys. Do not include markdown
fencing or any text outside the JSON object."""


def handler(event, context):
    """
    Build a prompt from pipeline context and invoke Bedrock.

    Args:
        event: Full pipeline state with $.normalized and $.enriched
        context: Lambda context (unused)

    Returns:
        dict with plan (structured analysis) and terraformSnippet
    """
    normalized = event["normalized"]
    enriched = event["enriched"]

    user_prompt = _build_user_prompt(normalized, enriched)

    logger.info(
        "Invoking Bedrock model=%s for resource=%s rule=%s",
        MODEL_ID,
        normalized["resourceId"],
        normalized["configRuleName"],
    )

    response = bedrock_client.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": MAX_TOKENS,
            "system": SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
        }),
    )

    response_body = json.loads(response["body"].read())
    raw_text = response_body["content"][0]["text"]

    plan = _parse_response(raw_text, normalized)

    logger.info(
        "Bedrock analysis complete: risk=%s snippet_length=%d",
        plan.get("RISK_ASSESSMENT", "UNKNOWN")[:50],
        len(plan.get("TERRAFORM_SNIPPET", "")),
    )

    return {
        "plan": plan,
        "terraformSnippet": plan.get("TERRAFORM_SNIPPET", ""),
    }


def _build_user_prompt(normalized, enriched):
    """
    Assemble the user prompt from drift context.

    Includes the normalized event, current resource config,
    and prior incident history if available.
    """
    sections = [
        "## Drift Event",
        f"Resource ID: {normalized['resourceId']}",
        f"Resource Type: {normalized['resourceType']}",
        f"Config Rule: {normalized['configRuleName']}",
        f"Region: {normalized['region']}",
        f"Severity: {normalized['severity']}",
        f"Annotation: {normalized['annotation']}",
        f"Previous Compliance: {normalized.get('previousCompliance', 'UNKNOWN')}",
        f"Detected At: {normalized['detectedAt']}",
        "",
        "## Current Resource Configuration",
        json.dumps(enriched.get("currentConfig", {}), indent=2),
    ]

    history = enriched.get("incidentHistory", [])
    if history:
        sections.append("")
        sections.append(
            f"## Prior Incident History ({len(history)} incidents)"
        )
        for i, incident in enumerate(history, 1):
            sections.append(
                f"\n### Incident {i}"
            )
            sections.append(json.dumps(incident, indent=2))

    return "\n".join(sections)


def _parse_response(raw_text, normalized):
    """
    Parse the Bedrock response as JSON.

    Falls back to a structured dict with the raw text
    if JSON parsing fails, so the pipeline does not break
    on malformed LLM output.
    """
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
    if raw_text.endswith("```"):
        raw_text = raw_text.rsplit("```", 1)[0].strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning(
            "Bedrock response for %s was not valid JSON, "
            "wrapping raw text as fallback",
            normalized["resourceId"],
        )
        return {
            "SUMMARY": "LLM response could not be parsed as JSON.",
            "RISK_ASSESSMENT": normalized.get("severity", "MEDIUM"),
            "LIKELY_CAUSE": "Unable to determine.",
            "REMEDIATION": raw_text,
            "TERRAFORM_SNIPPET": "",
        }
