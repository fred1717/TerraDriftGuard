{
  "Comment": "TerraDriftGuard - Drift detection to AI-powered remediation pipeline",
  "StartAt": "NormalizeEvent",
  "States": {
    "NormalizeEvent": {
      "Type": "Task",
      "Resource": "${NormalizeEventFunctionArn}",
      "Comment": "Extract and normalize fields from the raw Config compliance change event",
      "InputPath": "$",
      "ResultPath": "$.normalized",
      "Next": "EnrichResource",
      "Retry": [
        {
          "ErrorEquals": ["Lambda.ServiceException", "Lambda.TooManyRequestsException"],
          "IntervalSeconds": 2,
          "MaxAttempts": 3,
          "BackoffRate": 2.0
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "HandleFailure"
        }
      ]
    },

    "EnrichResource": {
      "Type": "Task",
      "Resource": "${EnrichResourceFunctionArn}",
      "Comment": "Fetch current resource configuration and prior incident history for Bedrock context",
      "InputPath": "$.normalized",
      "ResultPath": "$.enriched",
      "Next": "AssessSeverity",
      "Retry": [
        {
          "ErrorEquals": ["Lambda.ServiceException", "Lambda.TooManyRequestsException"],
          "IntervalSeconds": 2,
          "MaxAttempts": 3,
          "BackoffRate": 2.0
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "HandleFailure"
        }
      ]
    },

    "AssessSeverity": {
      "Type": "Choice",
      "Comment": "Route based on Config rule severity — critical rules skip straight to remediation",
      "Choices": [
        {
          "Variable": "$.normalized.configRuleName",
          "StringEquals": "restricted-ssh",
          "Next": "GenerateRemediation"
        },
        {
          "Variable": "$.normalized.configRuleName",
          "StringEquals": "s3-bucket-public-read-prohibited",
          "Next": "GenerateRemediation"
        },
        {
          "Variable": "$.normalized.configRuleName",
          "StringEquals": "iam-policy-no-statements-with-admin-access",
          "Next": "GenerateRemediation"
        }
      ],
      "Default": "GenerateRemediation"
    },


    "GenerateRemediation": {
      "Type": "Task",
      "Resource": "${GenerateRemediationFunctionArn}",
      "Comment": "Invoke Bedrock to produce a Terraform remediation plan from drift context",
      "InputPath": "$",
      "ResultPath": "$.remediation",
      "Next": "GenerateTerraform",
      "Retry": [
        {
          "ErrorEquals": ["Lambda.ServiceException", "Lambda.TooManyRequestsException"],
          "IntervalSeconds": 5,
          "MaxAttempts": 2,
          "BackoffRate": 2.0
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "HandleFailure"
        }
      ]
    },

    "GenerateTerraform": {
          "Type": "Task",
          "Resource": "${GenerateTerraformFunctionArn}",
          "Comment": "Assemble a complete, validatable Terraform file from the Bedrock snippet",
          "InputPath": "$",
          "ResultPath": "$.terraform",
          "Next": "StoreIncident",
          "Retry": [
            {
              "ErrorEquals": ["Lambda.ServiceException", "Lambda.TooManyRequestsException"],
              "IntervalSeconds": 2,
              "MaxAttempts": 3,
              "BackoffRate": 2.0
            }
          ],
          "Catch": [
            {
              "ErrorEquals": ["States.ALL"],
              "ResultPath": "$.error",
              "Next": "HandleFailure"
            }
          ]
        },

    "StoreIncident": {
      "Type": "Task",
      "Resource": "arn:aws:states:::dynamodb:putItem",
      "Comment": "Write the complete drift incident record to DynamoDB",
      "Parameters": {
        "TableName": "${DriftIncidentsTable}",
        "Item": {
          "drift_type": {"S.$": "$.normalized.configRuleName"},
          "timestamp": {"S.$": "$.normalized.detectedAt"},
          "resourceId": {"S.$": "$.normalized.resourceId"},
          "resourceType": {"S.$": "$.normalized.resourceType"},
          "region": {"S.$": "$.normalized.region"},
          "accountId": {"S.$": "$.normalized.accountId"},
          "annotation": {"S.$": "$.normalized.annotation"},
          "severity": {"S.$": "$.normalized.severity"},
          "currentConfig": {"S.$": "States.JsonToString($.enriched.currentConfig)"},
          "remediationPlan": {"S.$": "States.JsonToString($.remediation.plan)"},
          "terraformSnippet": {"S.$": "$.terraform.terraformFile"},
          "resolution_status": {"S": "OPEN"}
        }
      },
      "ResultPath": "$.dynamoResult",
      "Next": "ValidateAndEscalate",
      "Retry": [
        {
          "ErrorEquals": ["States.TaskFailed"],
          "IntervalSeconds": 2,
          "MaxAttempts": 3,
          "BackoffRate": 2.0
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "HandleFailure"
        }
      ]
    },

    "ValidateAndEscalate": {
          "Type": "Task",
          "Resource": "${ValidateAndEscalateFunctionArn}",
          "Comment": "Push remediation to GitHub as a PR and notify the ops team",
          "InputPath": "$",
          "ResultPath": "$.escalation",
          "Next": "Success",
          "Retry": [
            {
              "ErrorEquals": ["Lambda.ServiceException", "Lambda.TooManyRequestsException"],
              "IntervalSeconds": 2,
              "MaxAttempts": 3,
              "BackoffRate": 2.0
            }
          ],
          "Catch": [
            {
              "ErrorEquals": ["States.ALL"],
              "ResultPath": "$.error",
              "Next": "HandleFailure"
            }
          ]
        },

    "Success": {
      "Type": "Succeed",
      "Comment": "Drift incident fully processed, stored, and team notified"
    },

    "HandleFailure": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Comment": "Alert on pipeline failure so no drift incident is silently dropped",
      "Parameters": {
        "TopicArn": "${DriftAlertsTopic}",
        "Subject": "TerraDriftGuard Pipeline Failure",
        "Message.$": "States.Format('Pipeline failed. Error: {}', States.JsonToString($.error))"
      },
      "Next": "Failed"
    },

    "Failed": {
      "Type": "Fail",
      "Error": "PipelineError",
      "Cause": "One or more stages in the drift remediation pipeline failed. See HandleFailure notification for details."
    }
  }
}
