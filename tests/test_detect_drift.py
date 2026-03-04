"""
Tests for lambda/detect_drift/handler.py

Validates event normalization, severity mapping, and input rejection.
"""

import pytest

from detect_drift.handler import handler


class TestNormalization:
    """Verify correct field extraction from each sample event."""

    def test_sg_event_extracts_all_fields(self, sg_event):
        result = handler(sg_event, None)

        assert result["resourceId"] == "sg-0a1b2c3d4e5f67890"
        assert result["resourceType"] == "AWS::EC2::SecurityGroup"
        assert result["configRuleName"] == "restricted-ssh"
        assert result["region"] == "us-east-1"
        assert result["accountId"] == "123456789012"
        assert result["detectedAt"] == "2025-02-28T14:22:18.456Z"
        assert result["previousCompliance"] == "COMPLIANT"

    def test_s3_event_extracts_all_fields(self, s3_event):
        result = handler(s3_event, None)

        assert result["resourceId"] == "terradriftguard-artifacts-prod"
        assert result["resourceType"] == "AWS::S3::Bucket"
        assert result["configRuleName"] == "s3-bucket-public-read-prohibited"

    def test_iam_event_extracts_all_fields(self, iam_event):
        result = handler(iam_event, None)

        assert result["resourceId"] == "AROAEXAMPLEID12345"
        assert result["resourceType"] == "AWS::IAM::Role"
        assert result["configRuleName"] == "iam-policy-no-statements-with-admin-access"

    def test_annotation_preserved(self, sg_event):
        result = handler(sg_event, None)

        assert "port 22" in result["annotation"]
        assert "0.0.0.0/0" in result["annotation"]


class TestSeverityMapping:
    """Verify severity is assigned based on Config rule name."""

    def test_restricted_ssh_is_critical(self, sg_event):
        result = handler(sg_event, None)
        assert result["severity"] == "CRITICAL"

    def test_s3_public_read_is_high(self, s3_event):
        result = handler(s3_event, None)
        assert result["severity"] == "HIGH"

    def test_iam_admin_is_critical(self, iam_event):
        result = handler(iam_event, None)
        assert result["severity"] == "CRITICAL"

    def test_unknown_rule_defaults_to_medium(self, sg_event):
        sg_event["detail"]["configRuleName"] = "some-unknown-rule"
        result = handler(sg_event, None)
        assert result["severity"] == "MEDIUM"


class TestValidation:
    """Verify that invalid events are rejected."""

    def test_wrong_detail_type_raises(self, sg_event):
        sg_event["detail-type"] = "AWS API Call via CloudTrail"

        with pytest.raises(ValueError, match="Unexpected detail-type"):
            handler(sg_event, None)

    def test_compliant_event_raises(self, sg_event):
        sg_event["detail"]["newEvaluationResult"]["complianceType"] = "COMPLIANT"

        with pytest.raises(ValueError, match="not NON_COMPLIANT"):
            handler(sg_event, None)

    def test_missing_resource_id_raises(self, sg_event):
        del sg_event["detail"]["resourceId"]

        with pytest.raises(ValueError, match="Missing required fields"):
            handler(sg_event, None)

    def test_missing_detail_raises(self):
        event = {"detail-type": "Config Rules Compliance Change"}

        with pytest.raises(Exception):
            handler(event, None)
