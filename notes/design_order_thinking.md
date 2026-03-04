Pieces of pipeline to prioritise first. A few options:
- The DynamoDB table schema (Terraform resource definition + a documented attribute map)  
    It defines the incident record structure first means every Lambda knows what it's writing to, which prevents rework later.
- The Step Function state machine definition (an ASL (Amazon States Language) JSON file)  
    It builds the orchestration skeleton (even with placeholder Lambdas) gives a visual map of the entire workflow.  
    This clarifies what each function's inputs/outputs need to look like.
- The Bedrock remediation prompt ( a prompt template with variable placeholders)  
    This nails down the prompt template and expected output format early, since that's the novel/portfolio-worthy piece.
    It also shapes what data needs to flow through the pipeline.

The Step Function approach is arguably the strongest starting point because it forces the contract between every component to be defined upfront.  
Yet the DynamoDB schema is the safest if the goal is to avoid having to refactor data structures mid-build.

**Natural sequential step was writing the Intake Lambda**
An event comes in, so build the thing that catches it first seemed natural.  
Yet that is implementation-order thinking, not design-order thinking.  
Defining the Step Function skeleton or DynamoDB schema first is a top-down approach that prevents building components against assumptions that turn out wrong.

**Choosing between the DynamoDB table schema and the Step Function State Machine: best practice**
- The Step Function is the stronger starting point. It defines the data contract between every stage:
    - what the intake Lambda outputs
    - what Bedrock receives
    - what gets written to DynamoDB. 
    The schema naturally falls out of that.

- Starting with DynamoDB first means guessing at what fields the workflow will need before the workflow exists. 
    That's the rework risk mentioned earlier and the exact thing top-down design avoids.

**Step Function State Machine**
The Step Function ASL defines the DynamoDB item structure in the StoreIncident state.  

**DynamoDB table schema**
The DynamoDB table schema — partition key, sort key, GSI — is the natural next piece to formalize as a Terraform module under `terraform/modules/dynamodb/`.  
That locks in the data contract before any Lambda code gets written.

