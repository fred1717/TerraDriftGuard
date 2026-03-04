output "config_bucket_name" {
  description = "S3 bucket used by the Config delivery channel"
  value       = aws_s3_bucket.config.id
}

output "recorder_name" {
  description = "Name of the Config recorder"
  value       = aws_config_configuration_recorder.main.name
}

