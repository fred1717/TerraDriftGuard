output "state_machine_arn" {
  description = "ARN of the drift remediation state machine"
  value       = aws_sfn_state_machine.drift_remediation.arn
}

