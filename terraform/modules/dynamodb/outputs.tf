output "table_name" {
  description = "Name of the drift incidents table"
  value       = aws_dynamodb_table.drift_incidents.name
}

output "table_arn" {
  description = "ARN of the drift incidents table"
  value       = aws_dynamodb_table.drift_incidents.arn
}

output "gsi_arn" {
  description = "ARN of the resolution status GSI"
  value       = "${aws_dynamodb_table.drift_incidents.arn}/index/resolution-status-index"
}
