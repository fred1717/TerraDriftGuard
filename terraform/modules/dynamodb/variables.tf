variable "table_name" {
  description = "Name of the DynamoDB drift incidents table"
  type        = string
  default     = "terradriftguard-incidents"
}

variable "tags" {
  description = "Tags to apply to the DynamoDB table"
  type        = map(string)
  default     = {}
}
