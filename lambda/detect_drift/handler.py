"""
detect_drift handler

Normalizes a raw AWS Config compliance change event into the internal
schema expected by downstream Step Function states. This is the entry
point of the TerraDriftGuard pipeline.

Input:  Raw EventBridge event (detail-type: "Config Rules Compliance Change")
Output: Normalized dict written to $.normalized by the state machine
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Maps Config rule names to severity levels.
# Rules not listed here default to MEDIUM.
SEVERITY_MAP = {
    "restricted-ssh": "CRITICAL",
    "s3-bucket-public-read-prohibited": "HIGH",
    "iam-policy-no-statements-with-admin-access": "CRITICAL",
}


def handler(event, context):
    """
    Extract and normalize fields from a Config Rules Compliance Change event.

    Args:
        event: Raw EventBridge event dict
        context: Lambda context (unused)

    Returns:
        dict with normalized fields for the pipeline

    Raises:
        ValueError: If the event is not a compliance change to NON_COMPLIANT
    """
    logger.info("Received event: %s", event)

    detail = event.get("detail", {})

    _validate_event(event, detail)

    new_eval = detail["newEvaluationResult"]
    config_rule_name = detail["configRuleName"]

    normalized = {
        "resourceId": detail["resourceId"],
        "resourceType": detail["resourceType"],
        "configRuleName": config_rule_name,
        "region": detail["awsRegion"],
        "accountId": detail["awsAccountId"],
        "annotation": new_eval.get("annotation", "No annotation provided"),
        "detectedAt": new_eval.get(
            "resultRecordedTime",
            datetime.now(timezone.utc).isoformat()
        ),
        "severity": SEVERITY_MAP.get(config_rule_name, "MEDIUM"),
        "previousCompliance": detail.get(
            "oldEvaluationResult", {}
        ).get("complianceType", "UNKNOWN"),
    }

    logger.info(
        "Normalized event: resource=%s rule=%s severity=%s",
        normalized["resourceId"],
        normalized["configRuleName"],
        normalized["severity"],
    )

    return normalized


def _validate_event(event, detail):
    """Verify the event is a Config compliance change to NON_COMPLIANT."""

    detail_type = event.get("detail-type", "")
    if detail_type != "Config Rules Compliance Change":
        raise ValueError(
            f"Unexpected detail-type: {detail_type}"
        )

    new_eval = detail.get("newEvaluationResult", {})
    compliance = new_eval.get("complianceType", "")
    if compliance != "NON_COMPLIANT":
        raise ValueError(
            f"Event is not NON_COMPLIANT: {compliance}"
        )

    required_fields = [
        "resourceId",
        "resourceType",
        "configRuleName",
        "awsRegion",
        "awsAccountId",
    ]
    missing = [f for f in required_fields if f not in detail]
    if missing:
        raise ValueError(
            f"Missing required fields in detail: {missing}"
        )
