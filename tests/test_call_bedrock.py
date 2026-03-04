"""
Tests for lambda/call_bedrock/handler.py

Validates prompt construction, response parsing, and fallback behavior.
Mocks the Bedrock runtime client.
"""

import json

from unittest.mock import patch, MagicMock

import pytest

# noinspection PyProtectedMember
from call_bedrock.handler import handler, _build_user_prompt, _parse_response


@pytest.fixture
def bedrock_success_response():
    """Simulated successful Bedrock response with valid JSON."""
    body = json.dumps({
        "content": [
            {
                "text": json.dumps({
                    "SUMMARY": "SSH opened to the internet.",
                    "RISK_ASSESSMENT": "CRITICAL",
                    "LIKELY_CAUSE": "Manual console change.",
                    "REMEDIATION": "Remove 0.0.0.0/0 ingress on port 22.",
                    "TERRAFORM_SNIPPET": 'resource "aws_security_group_rule" "fix" {}',
                })
            }
        ]
    })
    mock_body = MagicMock()
    mock_body.read.return_value = body.encode()
    return {"body": mock_body}


@pytest.fixture
def bedrock_malformed_response():
    """Simulated Bedrock response with non-JSON text."""
    body = json.dumps({
        "content": [
            {"text": "Here is the fix: remove the SSH rule. Sorry, no JSON."}
        ]
    })
    mock_body = MagicMock()
    mock_body.read.return_value = body.encode()
    return {"body": mock_body}


class TestPromptConstruction:
    """Verify the user prompt includes all pipeline context."""

    def test_includes_normalized_fields(self, normalized_sg, enriched_sg):
        prompt = _build_user_prompt(normalized_sg, enriched_sg)

        assert "sg-0a1b2c3d4e5f67890" in prompt
        assert "restricted-ssh" in prompt
        assert "CRITICAL" in prompt
        assert "port 22" in prompt

    def test_includes_current_config(self, normalized_sg, enriched_sg):
        prompt = _build_user_prompt(normalized_sg, enriched_sg)

        assert "groupId" in prompt
        assert "ipPermissions" in prompt

    def test_includes_history_when_present(self, normalized_sg, enriched_sg):
        enriched_sg["incidentHistory"] = [
            {"drift_type": "restricted-ssh", "timestamp": "2025-02-20T10:00:00Z"}
        ]

        prompt = _build_user_prompt(normalized_sg, enriched_sg)

        assert "Prior Incident History" in prompt
        assert "2025-02-20" in prompt

    def test_omits_history_section_when_empty(self, normalized_sg, enriched_sg):
        prompt = _build_user_prompt(normalized_sg, enriched_sg)

        assert "Prior Incident History" not in prompt


class TestResponseParsing:
    """Verify JSON parsing and fallback behavior."""

    def test_valid_json_parsed(self):
        raw = json.dumps({"SUMMARY": "test", "TERRAFORM_SNIPPET": "resource {}"})
        result = _parse_response(raw, {"resourceId": "test"})

        assert result["SUMMARY"] == "test"

    def test_malformed_json_returns_fallback(self):
        result = _parse_response(
            "not json at all",
            {"resourceId": "test", "severity": "HIGH"},
        )

        assert result["SUMMARY"] == "LLM response could not be parsed as JSON."
        assert result["RISK_ASSESSMENT"] == "HIGH"
        assert "not json at all" in result["REMEDIATION"]
        assert result["TERRAFORM_SNIPPET"] == ""


class TestFullInvocation:
    """Verify end-to-end handler with mocked Bedrock."""

    @patch("call_bedrock.handler.bedrock_client")
    def test_successful_invocation(
        self, mock_bedrock, normalized_sg, enriched_sg, bedrock_success_response
    ):
        mock_bedrock.invoke_model.return_value = bedrock_success_response

        event = {"normalized": normalized_sg, "enriched": enriched_sg}
        result = handler(event, None)

        assert "plan" in result
        assert "terraformSnippet" in result
        assert result["plan"]["SUMMARY"] == "SSH opened to the internet."

    @patch("call_bedrock.handler.bedrock_client")
    def test_malformed_response_does_not_crash(
        self, mock_bedrock, normalized_sg, enriched_sg, bedrock_malformed_response
    ):
        mock_bedrock.invoke_model.return_value = bedrock_malformed_response

        event = {"normalized": normalized_sg, "enriched": enriched_sg}
        result = handler(event, None)

        assert result["plan"]["SUMMARY"] == "LLM response could not be parsed as JSON."
        assert result["terraformSnippet"] == ""
