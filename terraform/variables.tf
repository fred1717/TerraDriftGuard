variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB drift incidents table"
  type        = string
  default     = "terradriftguard-incidents"
}

variable "bedrock_model_id" {
  description = "Amazon Bedrock model ID for remediation reasoning"
  type        = string
  default     = "us.anthropic.claude-sonnet-4-20250514-v1:0"
}

variable "github_token_secret" {
  description = "Secrets Manager secret name containing the GitHub token"
  type        = string
  default     = ""
}

variable "github_repo_owner" {
  description = "GitHub repository owner"
  type        = string
  default     = "fred1717"
}

variable "github_repo_name" {
  description = "GitHub repository name"
  type        = string
  default     = "TerraDriftGuard"
}

variable "tags" {
  description = "Tags applied to all resources"
  type        = map(string)
  default = {
    Project   = "TerraDriftGuard"
    ManagedBy = "Terraform"
  }
}
