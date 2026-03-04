variable "detect_drift_function_arn" {
  description = "ARN of the detect_drift Lambda function"
  type        = string
}

variable "query_history_function_arn" {
  description = "ARN of the query_history Lambda function"
  type        = string
}

variable "call_bedrock_function_arn" {
  description = "ARN of the call_bedrock Lambda function"
  type        = string
}

variable "generate_terraform_function_arn" {
  description = "ARN of the generate_terraform Lambda function"
  type        = string
}

variable "validate_and_escalate_function_arn" {
  description = "ARN of the validate_and_escalate Lambda function"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB drift incidents table"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB drift incidents table"
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

