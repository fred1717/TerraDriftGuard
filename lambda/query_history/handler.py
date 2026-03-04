"""
query_history handler

Enriches a normalized drift event with two sources of context:
1. Current resource configuration from AWS Config
2. Previous incident history from DynamoDB (same drift type)

This gives downstream stages (especially Bedrock) the full picture:
what the resource looks like right now, and whether this has happened before.

Input:  $.normalized (from detect_drift)
Output: dict written to $.enriched by the state machine
"""

import json
import logging
import os

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

config_client = boto3.client("config")
dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ.get(
    "DRIFT_INCIDENTS_TABLE", "terradriftguard-incidents"
)
MAX_HISTORY_ITEMS = 5


def handler(event, context):
    """
    Fetch current resource configuration and prior incident history.

    Args:
        event: Normalized drift event dict from detect_drift
        context: Lambda context (unused)

    Returns:
        dict with currentConfig and incidentHistory
    """
    resource_id = event["resourceId"]
    resource_type = event["resourceType"]
    config_rule_name = event["configRuleName"]

    current_config = _get_current_config(resource_type, resource_id)
    incident_history = _get_incident_history(config_rule_name)

    enriched = {
        "currentConfig": current_config,
        "incidentHistory": incident_history,
        "historyCount": len(incident_history),
    }

    logger.info(
        "Enriched resource=%s: config_keys=%d, prior_incidents=%d",
        resource_id,
        len(current_config),
        len(incident_history),
    )

    return enriched


def _get_current_config(resource_type, resource_id):
    """
    Fetch the current configuration of a resource from AWS Config.

    Returns the parsed configuration dict, or a fallback dict
    if the resource is not tracked by Config.
    """
    try:
        response = config_client.get_resource_config_history(
            resourceType=resource_type,
            resourceId=resource_id,
            limit=1,
        )

        items = response.get("configurationItems", [])
        if not items:
            logger.warning(
                "No configuration items found for %s/%s",
                resource_type,
                resource_id,
            )
            return {"status": "NOT_FOUND", "resourceId": resource_id}

        item = items[0]
        config_str = item.get("configuration", "{}")

        if isinstance(config_str, str):
            try:
                return json.loads(config_str)
            except json.JSONDecodeError:
                return {"raw": config_str}

        return config_str

    except config_client.exceptions.ResourceNotDiscoveredException:
        logger.warning(
            "Resource not discovered by Config: %s/%s",
            resource_type,
            resource_id,
        )
        return {"status": "NOT_DISCOVERED", "resourceId": resource_id}

    except Exception as e:
        logger.error(
            "Failed to fetch config for %s/%s: %s",
            resource_type,
            resource_id,
            str(e),
        )
        return {"status": "ERROR", "error": str(e)}


def _get_incident_history(config_rule_name):
    """
    Query DynamoDB for previous incidents of the same drift type,
    ordered by most recent first.

    Returns a list of prior incident summaries for Bedrock context.
    """
    table = dynamodb.Table(TABLE_NAME)

    try:
        response = table.query(
            KeyConditionExpression=Key("drift_type").eq(config_rule_name),
            ScanIndexForward=False,
            Limit=MAX_HISTORY_ITEMS,
            ProjectionExpression=(
                "drift_type, #ts, resourceId, severity, "
                "resolution_status, annotation"
            ),
            ExpressionAttributeNames={"#ts": "timestamp"},
        )

        items = response.get("Items", [])

        logger.info(
            "Found %d prior incidents for drift_type=%s",
            len(items),
            config_rule_name,
        )

        return items

    except Exception as e:
        logger.error(
            "Failed to query incident history for %s: %s",
            config_rule_name,
            str(e),
        )
        return []
