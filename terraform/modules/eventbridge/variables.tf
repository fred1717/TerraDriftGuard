variable "state_machine_arn" {
  description = "ARN of the Step Functions state machine to trigger"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

