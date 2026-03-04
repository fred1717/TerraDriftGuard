variable "dynamodb_table_name" {
  description = "Name of the DynamoDB drift incidents table"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB drift incidents table"
  type        = string
}

variable "dynamodb_gsi_arn" {
  description = "ARN of the DynamoDB resolution status GSI"
  type        = string
}

variable "bedrock_model_id" {
  description = "Amazon Bedrock model ID for remediation reasoning"
  type        = string
  default     = "us.anthropic.claude-sonnet-4-20250514-v1:0"
}

variable "github_token_secret" {
  description = "Secrets Manager secret name containing the GitHub token"
  type        = string
}

variable "github_repo_owner" {
  description = "GitHub repository owner"
  type        = string
}

variable "github_repo_name" {
  description = "GitHub repository name"
  type        = string
}

variable "sns_topic_arn" {
  description = "ARN of the drift alerts SNS topic"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

