"""
Tests for lambda/validate_and_escalate/handler.py

Validates GitHub PR creation, SNS notification, and graceful degradation.
Mocks GitHub API, Secrets Manager, and SNS.
"""

import os

from unittest.mock import patch

import pytest

# noinspection PyProtectedMember
from validate_and_escalate.handler import (
    handler,
    _build_branch_name,
    _build_pr_body,
)


@pytest.fixture
def terraform_output(normalized_sg):
    """Simulated output of generate_terraform."""
    return {
        "terraformFile": 'provider "aws" {}\nresource "aws_security_group_rule" "fix" {}',
        "filename": "remediate_restricted_ssh_sg_0a1b2c3d4e5f67890.tf",
        "resourceId": normalized_sg["resourceId"],
        "configRuleName": normalized_sg["configRuleName"],
        "summary": "SSH opened to the internet.",
    }


@pytest.fixture
def full_state(normalized_sg, enriched_sg, remediation_sg, terraform_output):
    """Full pipeline state for validate_and_escalate."""
    return {
        "normalized": normalized_sg,
        "enriched": enriched_sg,
        "remediation": remediation_sg,
        "terraform": terraform_output,
    }


class TestBranchNameGeneration:
    """Verify branch naming format."""

    def test_includes_rule_and_resource(self, normalized_sg):
        branch = _build_branch_name(normalized_sg)

        assert branch.startswith("drift-fix/restricted-ssh/")
        assert "sg-0a1b2c3d4e5f67890" in branch

    def test_no_invalid_git_characters(self, normalized_sg):
        branch = _build_branch_name(normalized_sg)

        assert " " not in branch
        assert ".." not in branch


class TestPrBodyGeneration:
    """Verify PR description includes all context."""

    def test_includes_rule_name(self, normalized_sg, remediation_sg):
        body = _build_pr_body(normalized_sg, remediation_sg)

        assert "restricted-ssh" in body

    def test_includes_ai_analysis(self, normalized_sg, remediation_sg):
        body = _build_pr_body(normalized_sg, remediation_sg)

        assert "SSH port 22 opened" in body
        assert "CRITICAL" in body

    def test_includes_automation_notice(self, normalized_sg, remediation_sg):
        body = _build_pr_body(normalized_sg, remediation_sg)

        assert "generated automatically" in body


class TestGracefulDegradation:
    """Verify the handler completes even when services are unavailable."""

    @patch("validate_and_escalate.handler.sns_client")
    @patch("validate_and_escalate.handler._get_github_token", return_value=None)
    def test_skips_pr_without_token(self, _mock_token, _mock_sns, full_state):
        os.environ["DRIFT_ALERTS_TOPIC_ARN"] = ""
        _mock_sns.publish.return_value = {}

        result = handler(full_state, None)

        assert result["pr_url"] == "SKIPPED"
        assert result["filename"] is not None

    @patch("validate_and_escalate.handler.sns_client")
    @patch("validate_and_escalate.handler._get_github_token", return_value=None)
    def test_still_returns_branch_name(self, _mock_token, _mock_sns, full_state):
        os.environ["DRIFT_ALERTS_TOPIC_ARN"] = ""

        result = handler(full_state, None)

        assert result["branch"].startswith("drift-fix/")


class TestSnsNotification:
    """Verify SNS message content."""

    @patch("validate_and_escalate.handler.sns_client")
    @patch("validate_and_escalate.handler._get_github_token", return_value=None)
    @patch("validate_and_escalate.handler.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:test")
    def test_sends_notification_with_topic(self, _mock_token, _mock_sns, full_state):
        os.environ["DRIFT_ALERTS_TOPIC_ARN"] = "arn:aws:sns:us-east-1:123456789012:test"

        handler(full_state, None)

        _mock_sns.publish.assert_called_once()
        call_kwargs = _mock_sns.publish.call_args[1]
        assert "restricted-ssh" in call_kwargs["Subject"]
        assert "SKIPPED" not in call_kwargs["Subject"]

    @patch("validate_and_escalate.handler.sns_client")
    @patch("validate_and_escalate.handler._get_github_token", return_value=None)
    def test_skips_notification_without_topic(self, _mock_token, _mock_sns, full_state):
        os.environ["DRIFT_ALERTS_TOPIC_ARN"] = ""

        result = handler(full_state, None)

        _mock_sns.publish.assert_not_called()
        assert result["notification_sent"] is False
