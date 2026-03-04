terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ------------------------------------------------------------------------------
# SNS — drift alerts topic
# ------------------------------------------------------------------------------

resource "aws_sns_topic" "drift_alerts" {
  name = "terradriftguard-drift-alerts"
  tags = var.tags
}

# ------------------------------------------------------------------------------
# Config — recorder, delivery channel, and compliance rules
# ------------------------------------------------------------------------------

module "config" {
  source = "./modules/config"
  tags   = var.tags
}

# ------------------------------------------------------------------------------
# DynamoDB — drift incident tracking
# ------------------------------------------------------------------------------

module "dynamodb" {
  source     = "./modules/dynamodb"
  table_name = var.dynamodb_table_name
  tags       = var.tags
}

# ------------------------------------------------------------------------------
# Lambda — five pipeline functions
# ------------------------------------------------------------------------------

module "lambda" {
  source = "./modules/lambda"

  dynamodb_table_name = module.dynamodb.table_name
  dynamodb_table_arn  = module.dynamodb.table_arn
  dynamodb_gsi_arn    = module.dynamodb.gsi_arn

  bedrock_model_id    = var.bedrock_model_id
  github_token_secret = var.github_token_secret
  github_repo_owner   = var.github_repo_owner
  github_repo_name    = var.github_repo_name
  sns_topic_arn       = aws_sns_topic.drift_alerts.arn

  tags = var.tags
}

# ------------------------------------------------------------------------------
# Step Functions — pipeline orchestration
# ------------------------------------------------------------------------------

module "step_functions" {
  source = "./modules/step_functions"

  detect_drift_function_arn      = module.lambda.detect_drift_function_arn
  query_history_function_arn      = module.lambda.query_history_function_arn
  call_bedrock_function_arn = module.lambda.call_bedrock_function_arn
  generate_terraform_function_arn   = module.lambda.generate_terraform_function_arn
  validate_and_escalate_function_arn = module.lambda.validate_and_escalate_function_arn

  dynamodb_table_name = module.dynamodb.table_name
  dynamodb_table_arn  = module.dynamodb.table_arn

  sns_topic_arn = aws_sns_topic.drift_alerts.arn

  tags = var.tags
}

# ------------------------------------------------------------------------------
# EventBridge — Config compliance change to Step Functions
# ------------------------------------------------------------------------------

module "eventbridge" {
  source = "./modules/eventbridge"

  state_machine_arn = module.step_functions.state_machine_arn

  tags = var.tags
}

