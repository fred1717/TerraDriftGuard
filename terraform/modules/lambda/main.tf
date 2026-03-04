# ------------------------------------------------------------------------------
# Packaging — zip each Lambda directory
# ------------------------------------------------------------------------------

data "archive_file" "detect_drift" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/detect_drift"
  output_path = "${path.module}/zip/detect_drift.zip"
}

data "archive_file" "query_history" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/query_history"
  output_path = "${path.module}/zip/query_history.zip"
}

data "archive_file" "call_bedrock" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/call_bedrock"
  output_path = "${path.module}/zip/call_bedrock.zip"
}

data "archive_file" "generate_terraform" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/generate_terraform"
  output_path = "${path.module}/zip/generate_terraform.zip"
}

data "archive_file" "validate_and_escalate" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/validate_and_escalate"
  output_path = "${path.module}/zip/validate_and_escalate.zip"
}

# ------------------------------------------------------------------------------
# Lambda functions
# ------------------------------------------------------------------------------

resource "aws_lambda_function" "detect_drift" {
  function_name    = "terradriftguard-detect-drift"
  role             = aws_iam_role.detect_drift.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 30
  filename         = data.archive_file.detect_drift.output_path
  source_code_hash = data.archive_file.detect_drift.output_base64sha256
  tags             = var.tags
}

resource "aws_lambda_function" "query_history" {
  function_name    = "terradriftguard-query-history"
  role             = aws_iam_role.query_history.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 30
  filename         = data.archive_file.query_history.output_path
  source_code_hash = data.archive_file.query_history.output_base64sha256

  environment {
    variables = {
      DRIFT_INCIDENTS_TABLE = var.dynamodb_table_name
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "call_bedrock" {
  function_name    = "terradriftguard-call-bedrock"
  role             = aws_iam_role.call_bedrock.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 120
  filename         = data.archive_file.call_bedrock.output_path
  source_code_hash = data.archive_file.call_bedrock.output_base64sha256

  environment {
    variables = {
      BEDROCK_MODEL_ID = var.bedrock_model_id
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "generate_terraform" {
  function_name    = "terradriftguard-generate-terraform"
  role             = aws_iam_role.generate_terraform.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 30
  filename         = data.archive_file.generate_terraform.output_path
  source_code_hash = data.archive_file.generate_terraform.output_base64sha256
  tags             = var.tags
}

resource "aws_lambda_function" "validate_and_escalate" {
  function_name    = "terradriftguard-validate-and-escalate"
  role             = aws_iam_role.validate_and_escalate.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 60
  filename         = data.archive_file.validate_and_escalate.output_path
  source_code_hash = data.archive_file.validate_and_escalate.output_base64sha256

  environment {
    variables = {
      GITHUB_TOKEN_SECRET    = var.github_token_secret
      GITHUB_REPO_OWNER      = var.github_repo_owner
      GITHUB_REPO_NAME       = var.github_repo_name
      DRIFT_ALERTS_TOPIC_ARN = var.sns_topic_arn
    }
  }

  tags = var.tags
}

# ------------------------------------------------------------------------------
# IAM roles — one per function, least privilege
# ------------------------------------------------------------------------------

resource "aws_iam_role" "detect_drift" {
  name               = "terradriftguard-detect-drift-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = var.tags
}

resource "aws_iam_role" "query_history" {
  name               = "terradriftguard-query-history-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = var.tags
}

resource "aws_iam_role" "call_bedrock" {
  name               = "terradriftguard-call-bedrock-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = var.tags
}

resource "aws_iam_role" "generate_terraform" {
  name               = "terradriftguard-generate-terraform-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = var.tags
}

resource "aws_iam_role" "validate_and_escalate" {
  name               = "terradriftguard-validate-and-escalate-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# ------------------------------------------------------------------------------
# Shared policy — CloudWatch Logs for all five functions
# ------------------------------------------------------------------------------

resource "aws_iam_role_policy_attachment" "detect_drift_logs" {
  role       = aws_iam_role.detect_drift.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "query_history_logs" {
  role       = aws_iam_role.query_history.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "call_bedrock_logs" {
  role       = aws_iam_role.call_bedrock.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "generate_terraform_logs" {
  role       = aws_iam_role.generate_terraform.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "validate_and_escalate_logs" {
  role       = aws_iam_role.validate_and_escalate.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ------------------------------------------------------------------------------
# Function-specific policies
# ------------------------------------------------------------------------------

# query_history: read Config + read DynamoDB
resource "aws_iam_role_policy" "query_history_config" {
  name = "config-read"
  role = aws_iam_role.query_history.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "config:GetResourceConfigHistory"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "query_history_dynamodb" {
  name = "dynamodb-read"
  role = aws_iam_role.query_history.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Query"
        ]
        Resource = [
          var.dynamodb_table_arn,
          var.dynamodb_gsi_arn,
        ]
      }
    ]
  })
}

# call_bedrock: invoke model
resource "aws_iam_role_policy" "call_bedrock_invoke" {
  name = "bedrock-invoke"
  role = aws_iam_role.call_bedrock.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "bedrock:InvokeModel"
        Resource = [
          "arn:aws:bedrock:us-east-1:${data.aws_caller_identity.current.account_id}:inference-profile/${var.bedrock_model_id}",
          "arn:aws:bedrock:*::foundation-model/${trimprefix(var.bedrock_model_id, "us.")}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "aws-marketplace:ViewSubscriptions",
          "aws-marketplace:Subscribe"
        ]
        Resource = "*"
      }
    ]
  })
}

# validate_and_escalate: read Secrets Manager + publish SNS
resource "aws_iam_role_policy" "validate_and_escalate_secrets" {
  name = "secrets-read"
  role = aws_iam_role.validate_and_escalate.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = "arn:aws:secretsmanager:*:*:secret:${var.github_token_secret}-*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "validate_and_escalate_sns" {
  name = "sns-publish"
  role = aws_iam_role.validate_and_escalate.id

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

data "aws_caller_identity" "current" {}
