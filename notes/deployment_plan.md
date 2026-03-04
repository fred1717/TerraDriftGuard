The plan remains the same. Rough breakdown:
- `terraform apply` + verify all resources provisioned correctly — 1–2 hours. The usual friction points are:
    - IAM issues
    - Config rule setup
- Trigger live drift events, which consists in manually modifying in the console (around 30 minutes):
    - a security group
    - an S3 bucket
    - an IAM role
- Wait for Config to detect and evaluate — this is the variable part.  
    Config can take 5–15 minutes per evaluation, sometimes longer.  
    Budget 1–2 hours of wall clock time including debugging if the pipeline doesn't trigger as expected.
- Verify full pipeline execution — 1–2 hours, more if things need fixing:
    - Step Functions visual
    - DynamoDB record
    - Bedrock response
    - GitHub PR
    - SNS notification
- Capture screenshots for evidence/screenshots/ — 30 minutes
- terraform destroy — 15 minutes

Roughly 4–8 hours of active work, but it could be stretched to a full day because of:
- Config evaluation delays
- inevitable first-deploy debugging  
The 1–2 day window is therefore realistic.
