resource "aws_sfn_state_machine" "drift_remediation" {
  name     = "terradriftguard-drift-remediation"
  role_arn = aws_iam_role.step_functions.arn

  definition = templatefile("${path.module}/drift_remediation.asl", {
    NormalizeEventFunctionArn      = var.detect_drift_function_arn
    EnrichResourceFunctionArn      = var.query_history_function_arn
    GenerateRemediationFunctionArn = var.call_bedrock_function_arn
    GenerateTerraformFunctionArn   = var.generate_terraform_function_arn
    ValidateAndEscalateFunctionArn = var.validate_and_escalate_function_arn
    DriftIncidentsTable            = var.dynamodb_table_name
    DriftAlertsTopic               = var.sns_topic_arn
  })

  tags = var.tags
}

resource "aws_iam_role" "step_functions" {
  name = "terradriftguard-step-functions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "step_functions_invoke_lambda" {
  name = "invoke-lambda"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "lambda:InvokeFunction"
        Resource = [
          var.detect_drift_function_arn,
          var.query_history_function_arn,
          var.call_bedrock_function_arn,
          var.generate_terraform_function_arn,
          var.validate_and_escalate_function_arn,
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "step_functions_dynamodb" {
  name = "dynamodb-put"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "dynamodb:PutItem"
        Resource = var.dynamodb_table_arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "step_functions_sns" {
  name = "sns-publish"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = var.sns_topic_arn
      }
    ]
  })
}

