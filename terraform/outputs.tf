output "state_machine_arn" {
  description = "ARN of the Step Functions state machine"
  value       = module.step_functions.state_machine_arn
}

output "dynamodb_table_name" {
  description = "Name of the drift incidents DynamoDB table"
  value       = module.dynamodb.table_name
}

output "sns_topic_arn" {
  description = "ARN of the drift alerts SNS topic"
  value       = aws_sns_topic.drift_alerts.arn
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule triggering the pipeline"
  value       = module.eventbridge.rule_arn
}

