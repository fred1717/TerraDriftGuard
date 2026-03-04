output "detect_drift_function_arn" {
  description = "ARN of the detect_drift Lambda function"
  value       = aws_lambda_function.detect_drift.arn
}

output "query_history_function_arn" {
  description = "ARN of the query_history Lambda function"
  value       = aws_lambda_function.query_history.arn
}

output "call_bedrock_function_arn" {
  description = "ARN of the call_bedrock Lambda function"
  value       = aws_lambda_function.call_bedrock.arn
}

output "generate_terraform_function_arn" {
  description = "ARN of the generate_terraform Lambda function"
  value       = aws_lambda_function.generate_terraform.arn
}

output "validate_and_escalate_function_arn" {
  description = "ARN of the validate_and_escalate Lambda function"
  value       = aws_lambda_function.validate_and_escalate.arn
}

