resource "aws_cloudwatch_event_rule" "config_compliance_change" {
  name        = "terradriftguard-config-compliance-change"
  description = "Triggers the drift remediation pipeline on Config compliance changes"

  event_pattern = jsonencode({
    source      = ["aws.config"]
    detail-type = ["Config Rules Compliance Change"]
    detail = {
      messageType = ["ComplianceChangeNotification"]
      newEvaluationResult = {
        complianceType = ["NON_COMPLIANT"]
      }
    }
  })

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "step_functions" {
  rule     = aws_cloudwatch_event_rule.config_compliance_change.name
  arn      = var.state_machine_arn
  role_arn = aws_iam_role.eventbridge.arn
}

resource "aws_iam_role" "eventbridge" {
  name = "terradriftguard-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "eventbridge_start_execution" {
  name = "start-step-functions"
  role = aws_iam_role.eventbridge.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "states:StartExecution"
        Resource = var.state_machine_arn
      }
    ]
  })
}

