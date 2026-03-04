2–3 realistic AWS Config compliance change events that represent common manual drift scenarios.  
These drift scenarios cover the classic "someone went into the console" situations:  
- `sg_open_ssh.json` — The restricted-ssh Config rule catches a security group that just had port 22 opened to 0.0.0.0/0. COMPLIANT → NON_COMPLIANT.
- `s3_public_read.json` — The s3-bucket-public-read-prohibited rule flags a bucket where `BlockPublicAccess` was disabled and a GetObject wildcard principal policy was added. COMPLIANT → NON_COMPLIANT.
- `iam_admin_policy.json` — The iam-policy-no-statements-with-admin-access rule catches `AdministratorAccess` being attached to an execution role. COMPLIANT → NON_COMPLIANT.  

All three use the real `EventBridge` envelope structure (Config Rules Compliance Change detail-type) with both `oldEvaluationResult` and `newEvaluationResult`.  
That way, the downstream Lambda and Step Functions have the full compliance transition to work with.  
The annotation field in each carries the human-readable explanation that `Bedrock` can later use as context for remediation reasoning.  

These are simulated AWS Config events — the exact JSON that `EventBridge` would emit when a resource goes from COMPLIANT to NON_COMPLIANT.  
They serve as test inputs for the TerraDriftGuard pipeline, letting each Lambda and Step Function be developed and validated locally before deploying anything.



