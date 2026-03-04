```text
TerraDriftGuard/
    .gitignore
    pytest.ini
    README.md
    requirements-dev.txt

    docs/
        architecture_decisions.md
        queries.md
        repository_structure.md

        diagrams/
    

    evidence/
        cli/
            config-iam-noncompliant.json
            config-sg-noncompliant.json
            config-sg-noncompliant.json
            dynamodb-all-incidents.txt
            iam_admin_policy.txt
            s3_public_read.txt
            sample_drift_event.txt
            sg-open-ssh-describe.json
            sg_open_ssh.txt

        screenshots/
            config-rules-overview-all-noncompliant.png
            dynamodb-incidents-left.png
            dynamodb-incidents-right.png
            s3-bucket-permissions-public-read.png
            step-functions-execution-list-final.png
            step-functions-graph-iam-admin-policy.png
            step-functions-graph-s3-public-read.png
            step-functions-graph-success.png
            step-functions-input-output-iam-admin-policy.png
            step-functions-input-output-s3-public-read.png


    .github/
        workflows/
            terraform-validate.yml


    lambda/
        call_bedrock/
            __init__.py
            handler.py
            requirements.txt

        detect_drift/
            __init__.py
            handler.py
            requirements.txt

        generate_terraform/
            __init__.py
            handler.py
            requirements.txt

        query_history/
            __init__.py
            handler.py
            requirements.txt

        validate_and_escalate/
            __init__.py
            handler.py
            requirements.txt


    notes/
        design_order_thinking.md
    

    scripts/
        format_dynamodb.py
        format_evidence.py


    terraform/
        .terraform.lock.hcl
        main.tf
        variables.tf
        outputs.tf
        terraform.tfstate
        terraform.tfstate.backup
        terraform.tfvars.example

        modules/
            config/
                main.tf
                outputs.tf
                variables.tf

            dynamodb/
                main.tf
                outputs.tf
                variables.tf

            eventbridge/
                main.tf
                outputs.tf
                variables.tf

            lambda/
                main.tf
                outputs.tf
                variables.tf

            step_functions/
                drift_remediation.asl
                main.tf
                outputs.tf
                variables.tf
        
    
    tests/
        conftest.py
        test_call_bedrock.py
        test_detect_drift.py
        test_generate_terraform.py
        test_query_history.py
        test_validate_and_escalate.py

        events/
            README.md
            iam_admin_policy.json
            sample_drift_event.json
            sg_open_ssh.json
            s3_public_read.json
    





```



