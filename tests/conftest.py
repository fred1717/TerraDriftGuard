"""
Shared fixtures for TerraDriftGuard unit tests.

Loads the sample Config compliance change events from tests/events/
and provides normalized output fixtures for downstream handler tests.
"""

import json

import os

import pytest

EVENTS_DIR = os.path.join(os.path.dirname(__file__), "events")


def _load_event(filename):
    with open(os.path.join(EVENTS_DIR, filename)) as f:
        return json.load(f)


@pytest.fixture
def sg_event():
    return _load_event("sg_open_ssh.json")


@pytest.fixture
def s3_event():
    return _load_event("S3_public_read.json")


@pytest.fixture
def iam_event():
    return _load_event("iam_admin_policy.json")


@pytest.fixture
def normalized_sg():
    """Expected output of detect_drift for the security group event."""
    return {
        "resourceId": "sg-0a1b2c3d4e5f67890",
        "resourceType": "AWS::EC2::SecurityGroup",
        "configRuleName": "restricted-ssh",
        "region": "us-east-1",
        "accountId": "123456789012",
        "annotation": (
            "Security group sg-0a1b2c3d4e5f67890 has an inbound rule "
            "allowing SSH (port 22) from 0.0.0.0/0."
        ),
        "detectedAt": "2025-02-28T14:22:18.456Z",
        "severity": "CRITICAL",
        "previousCompliance": "COMPLIANT",
    }


@pytest.fixture
def enriched_sg():
    """Simulated output of query_history for downstream tests."""
    return {
        "currentConfig": {
            "groupId": "sg-0a1b2c3d4e5f67890",
            "ipPermissions": [
                {
                    "fromPort": 22,
                    "toPort": 22,
                    "ipProtocol": "tcp",
                    "ipRanges": [{"cidrIp": "0.0.0.0/0"}],
                }
            ],
        },
        "incidentHistory": [],
        "historyCount": 0,
    }


@pytest.fixture
def remediation_sg():
    """Simulated output of call_bedrock for downstream tests."""
    return {
        "plan": {
            "SUMMARY": "SSH port 22 opened to the internet on sg-0a1b2c3d4e5f67890.",
            "RISK_ASSESSMENT": "CRITICAL - allows unauthorized SSH access from any IP.",
            "LIKELY_CAUSE": "Manual console change, likely debugging.",
            "REMEDIATION": "Remove the 0.0.0.0/0 ingress rule on port 22.",
            "TERRAFORM_SNIPPET": (
                'resource "aws_security_group_rule" "ssh_restricted" {\n'
                "  type              = \"ingress\"\n"
                "  from_port         = 22\n"
                "  to_port           = 22\n"
                "  protocol          = \"tcp\"\n"
                "  cidr_blocks       = [\"10.0.0.0/8\"]\n"
                "  security_group_id = \"sg-0a1b2c3d4e5f67890\"\n"
                "}"
            ),
        },
        "terraformSnippet": (
            'resource "aws_security_group_rule" "ssh_restricted" {\n'
            "  type              = \"ingress\"\n"
            "  from_port         = 22\n"
            "  to_port           = 22\n"
            "  protocol          = \"tcp\"\n"
            "  cidr_blocks       = [\"10.0.0.0/8\"]\n"
            "  security_group_id = \"sg-0a1b2c3d4e5f67890\"\n"
            "}"
        ),
    }


@pytest.fixture
def full_pipeline_state(normalized_sg, enriched_sg, remediation_sg):
    """Full pipeline state as seen by generate_terraform and validate_and_escalate."""
    return {
        "normalized": normalized_sg,
        "enriched": enriched_sg,
        "remediation": remediation_sg,
    }
