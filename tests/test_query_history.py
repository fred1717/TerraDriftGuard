"""
Tests for lambda/query_history/handler.py

Validates Config enrichment and DynamoDB history queries.
Mocks AWS service calls since tests run locally.
"""

import json

from unittest.mock import MagicMock, patch

import pytest

from query_history.handler import handler


@pytest.fixture
def mock_config_response():
    """Simulated response from config:GetResourceConfigHistory."""
    return {
        "configurationItems": [
            {
                "configuration": json.dumps({
                    "groupId": "sg-0a1b2c3d4e5f67890",
                    "ipPermissions": [
                        {
                            "fromPort": 22,
                            "toPort": 22,
                            "ipProtocol": "tcp",
                            "ipRanges": [{"cidrIp": "0.0.0.0/0"}],
                        }
                    ],
                })
            }
        ]
    }


@pytest.fixture
def mock_dynamodb_response():
    """Simulated response from DynamoDB query."""
    return {
        "Items": [
            {
                "drift_type": "restricted-ssh",
                "timestamp": "2025-02-20T10:00:00Z",
                "resourceId": "sg-0a1b2c3d4e5f67890",
                "severity": "CRITICAL",
                "resolution_status": "RESOLVED",
                "annotation": "Previous SSH drift incident",
            }
        ]
    }


class TestConfigEnrichment:
    """Verify current resource configuration is fetched and parsed."""

    @patch("query_history.handler.config_client")
    @patch("query_history.handler.dynamodb")
    def test_returns_parsed_config(
        self, mock_dynamo, mock_config, normalized_sg, mock_config_response
    ):
        mock_config.get_resource_config_history.return_value = mock_config_response
        mock_table = MagicMock()
        mock_table.query.return_value = {"Items": []}
        mock_dynamo.Table.return_value = mock_table

        result = handler(normalized_sg, None)

        assert result["currentConfig"]["groupId"] == "sg-0a1b2c3d4e5f67890"
        assert len(result["currentConfig"]["ipPermissions"]) == 1

    @patch("query_history.handler.config_client")
    @patch("query_history.handler.dynamodb")
    def test_handles_missing_config(self, mock_dynamo, mock_config, normalized_sg):
        mock_config.get_resource_config_history.return_value = {
            "configurationItems": []
        }
        mock_table = MagicMock()
        mock_table.query.return_value = {"Items": []}
        mock_dynamo.Table.return_value = mock_table

        result = handler(normalized_sg, None)

        assert result["currentConfig"]["status"] == "NOT_FOUND"

    @patch("query_history.handler.config_client")
    @patch("query_history.handler.dynamodb")
    def test_handles_config_api_error(self, mock_dynamo, mock_config, normalized_sg):
        mock_config.exceptions.ResourceNotDiscoveredException = type(
            "ResourceNotDiscoveredException", (Exception,), {}
        )
        mock_config.get_resource_config_history.side_effect = Exception("API timeout")
        mock_table = MagicMock()
        mock_table.query.return_value = {"Items": []}
        mock_dynamo.Table.return_value = mock_table

        result = handler(normalized_sg, None)

        assert result["currentConfig"]["status"] == "ERROR"
        assert "API timeout" in result["currentConfig"]["error"]


class TestIncidentHistory:
    """Verify DynamoDB history query and response shaping."""

    @patch("query_history.handler.config_client")
    @patch("query_history.handler.dynamodb")
    def test_returns_prior_incidents(
        self, mock_dynamo, mock_config, normalized_sg,
        mock_config_response, mock_dynamodb_response
    ):
        mock_config.get_resource_config_history.return_value = mock_config_response
        mock_table = MagicMock()
        mock_table.query.return_value = mock_dynamodb_response
        mock_dynamo.Table.return_value = mock_table

        result = handler(normalized_sg, None)

        assert result["historyCount"] == 1
        assert result["incidentHistory"][0]["drift_type"] == "restricted-ssh"

    @patch("query_history.handler.config_client")
    @patch("query_history.handler.dynamodb")
    def test_empty_history(self, mock_dynamo, mock_config, normalized_sg, mock_config_response):
        mock_config.get_resource_config_history.return_value = mock_config_response
        mock_table = MagicMock()
        mock_table.query.return_value = {"Items": []}
        mock_dynamo.Table.return_value = mock_table

        result = handler(normalized_sg, None)

        assert result["historyCount"] == 0
        assert result["incidentHistory"] == []

    @patch("query_history.handler.config_client")
    @patch("query_history.handler.dynamodb")
    def test_dynamodb_error_returns_empty(
        self, mock_dynamo, mock_config, normalized_sg, mock_config_response
    ):
        mock_config.get_resource_config_history.return_value = mock_config_response
        mock_table = MagicMock()
        mock_table.query.side_effect = Exception("DynamoDB timeout")
        mock_dynamo.Table.return_value = mock_table

        result = handler(normalized_sg, None)

        assert result["incidentHistory"] == []
        assert result["historyCount"] == 0
