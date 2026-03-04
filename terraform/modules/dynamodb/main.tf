resource "aws_dynamodb_table" "drift_incidents" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "drift_type"
  range_key = "timestamp"

  attribute {
    name = "drift_type"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "resolution_status"
    type = "S"
  }

  global_secondary_index {
    name            = "resolution-status-index"
    hash_key        = "resolution_status"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = false
  }

  tags = var.tags
}
