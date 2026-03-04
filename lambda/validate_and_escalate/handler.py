"""
validate_and_escalate handler

Takes the assembled Terraform remediation file and:
1. Pushes it to a new branch in the GitHub repository
2. Opens a pull request with drift context in the description
3. Publishes an SNS notification to the ops team

Terraform validation (terraform validate + terraform plan) is handled
by the GitHub Actions workflow triggered on PR creation, not inside
this Lambda.

Input:  Full pipeline state ($.normalized + $.enriched + $.remediation + $.terraform)
Output: dict with PR URL, branch name, and notification status
"""

import json
import logging
import os
import re
from datetime import datetime, timezone

import boto3
import urllib3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

http = urllib3.PoolManager()
sns_client = boto3.client("sns")

GITHUB_API = "https://api.github.com"
REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER", "fred1717")
REPO_NAME = os.environ.get("GITHUB_REPO_NAME", "TerraDriftGuard")
BASE_BRANCH = os.environ.get("GITHUB_BASE_BRANCH", "main")
SNS_TOPIC_ARN = os.environ.get("DRIFT_ALERTS_TOPIC_ARN", "")


def handler(event, context):
    """
    Push remediation file to GitHub and notify the team.

    Args:
        event: Full pipeline state
        context: Lambda context (unused)

    Returns:
        dict with pr_url, branch, and notification details
    """
    normalized = event["normalized"]
    terraform = event["terraform"]
    remediation = event["remediation"]

    github_token = _get_github_token()

    branch_name = _build_branch_name(normalized)
    filename = terraform["filename"]
    file_content = terraform["terraformFile"]
    pr_body = _build_pr_body(normalized, remediation)

    pr_url = None
    if github_token:
        sha = _get_base_branch_sha(github_token)
        _create_branch(github_token, branch_name, sha)
        _push_file(github_token, branch_name, filename, file_content)
        pr_url = _create_pull_request(
            github_token,
            branch_name,
            normalized,
            pr_body,
        )
        logger.info("Pull request created: %s", pr_url)
    else:
        logger.warning(
            "No GitHub token available, skipping PR creation"
        )

    notification = _send_notification(
        normalized, terraform, remediation, pr_url
    )

    return {
        "pr_url": pr_url or "SKIPPED",
        "branch": branch_name,
        "filename": filename,
        "notification_sent": notification,
    }


def _get_github_token():
    """
    Retrieve GitHub token from AWS Secrets Manager.

    Returns None if the secret is not configured,
    allowing the pipeline to complete without PR creation.
    """
    secret_name = os.environ.get("GITHUB_TOKEN_SECRET", "")
    if not secret_name:
        return None

    try:
        secrets_client = boto3.client("secretsmanager")
        response = secrets_client.get_secret_value(
            SecretId=secret_name
        )
        return response["SecretString"]
    except Exception as e:
        logger.error("Failed to retrieve GitHub token: %s", str(e))
        return None


def _build_branch_name(normalized):
    """Generate a branch name from the drift event."""
    rule = normalized["configRuleName"]
    resource = normalized["resourceId"]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    safe_resource = re.sub(r"[^a-zA-Z0-9_-]", "_", resource)
    return f"drift-fix/{rule}/{safe_resource}-{timestamp}"


def _build_pr_body(normalized, remediation):
    """Assemble a pull request description from pipeline context."""
    plan = remediation.get("plan", {})

    sections = [
        "## TerraDriftGuard Automated Remediation",
        "",
        f"**Config Rule:** `{normalized['configRuleName']}`",
        f"**Resource:** `{normalized['resourceType']}` / `{normalized['resourceId']}`",
        f"**Region:** `{normalized['region']}`",
        f"**Severity:** {normalized['severity']}",
        f"**Detected:** {normalized['detectedAt']}",
        "",
        "### Annotation",
        normalized.get("annotation", "No annotation provided"),
        "",
        "### AI Analysis",
        f"**Summary:** {plan.get('SUMMARY', 'N/A')}",
        f"**Risk:** {plan.get('RISK_ASSESSMENT', 'N/A')}",
        f"**Likely Cause:** {plan.get('LIKELY_CAUSE', 'N/A')}",
        f"**Remediation:** {plan.get('REMEDIATION', 'N/A')}",
        "",
        "---",
        "*This PR was generated automatically by TerraDriftGuard.*",
        "*Review the proposed changes before merging.*",
    ]

    return "\n".join(sections)


def _github_request(method, path, token, body=None):
    """Make an authenticated GitHub API request."""
    url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    encoded_body = None
    if body is not None:
        encoded_body = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    response = http.request(
        method, url, headers=headers, body=encoded_body
    )

    if response.status >= 400:
        logger.error(
            "GitHub API error: %s %s -> %d: %s",
            method, path, response.status, response.data.decode()
        )
        raise RuntimeError(
            f"GitHub API returned {response.status} for {method} {path}"
        )

    return json.loads(response.data.decode())


def _get_base_branch_sha(token):
    """Get the latest commit SHA of the base branch."""
    data = _github_request(
        "GET", f"/git/ref/heads/{BASE_BRANCH}", token
    )
    return data["object"]["sha"]


def _create_branch(token, branch_name, sha):
    """Create a new branch from the given SHA."""
    _github_request("POST", "/git/refs", token, {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha,
    })
    logger.info("Created branch: %s", branch_name)


def _push_file(token, branch_name, filename, content):
    """Push the Terraform file to the branch."""
    import base64
    encoded = base64.b64encode(content.encode()).decode()

    _github_request(
        "PUT",
        f"/contents/remediations/{filename}",
        token,
        {
            "message": f"drift-fix: {filename}",
            "content": encoded,
            "branch": branch_name,
        },
    )
    logger.info("Pushed file: remediations/%s", filename)


def _create_pull_request(token, branch_name, normalized, body):
    """Open a pull request and return its URL."""
    title = (
        f"[TerraDriftGuard] {normalized['configRuleName']} - "
        f"{normalized['resourceId']}"
    )

    data = _github_request("POST", "/pulls", token, {
        "title": title,
        "head": branch_name,
        "base": BASE_BRANCH,
        "body": body,
    })

    return data.get("html_url", "")


def _send_notification(normalized, terraform, remediation, pr_url):
    """Publish drift alert to SNS."""
    if not SNS_TOPIC_ARN:
        logger.warning("No SNS topic ARN configured, skipping notification")
        return False

    plan = remediation.get("plan", {})

    message = "\n".join([
        f"Drift Detected: {normalized['resourceType']} / {normalized['resourceId']}",
        f"Rule: {normalized['configRuleName']}",
        f"Severity: {normalized['severity']}",
        f"Annotation: {normalized['annotation']}",
        "",
        f"AI Summary: {plan.get('SUMMARY', 'N/A')}",
        f"Risk: {plan.get('RISK_ASSESSMENT', 'N/A')}",
        "",
        f"Remediation File: {terraform['filename']}",
        f"Pull Request: {pr_url or 'Not created'}",
    ])

    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Drift Detected: {normalized['configRuleName']} - {normalized['resourceId']}",
            Message=message,
        )
        logger.info("SNS notification sent")
        return True
    except Exception as e:
        logger.error("Failed to send SNS notification: %s", str(e))
        return False
