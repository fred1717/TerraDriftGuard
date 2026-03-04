## 1. Background / Context
### 1.1 Gemini recommendations
#### 1.1.1 THE AGENTIC SRE PROJECT
**Goal:**  
Build a "Self-Healing" Agent that monitors the Dark VPC and generates/executes Terraform fixes.

**Intelligence Layer:**  
Model-Agnostic using `LiteLLM`.

**Primary Brain:**  
Claude Opus 4.6 (via Direct API/Secrets Manager) for "Adaptive Thinking" reasoning.

**Secondary Brain:**  
Gemini 2.0/3.0 Flash (via AI Studio/API) for massive context/log summarizing.

#### 1.1.2 TECHNICAL CONSTRAINTS FOR THE AGENT
**Language:**  
- Python (Lambda) 
- HCL (Terraform).

**Security:**  
`API Keys` for Anthropic/Gemini must stay in `AWS Secrets Manager`.

**Budget:**  
Must cost near-zero when idle (Serverless).

How to use this in Google AI Studio: Open aistudio.google.com.  
- Start a New Chat and paste the block above into the System Instructions (the top-left text area).
- Upload Your Files: Click the "+" (Add Files) button. Since AI Studio allows you to upload Folders, you can upload your entire "ITF Masters" Terraform folder.
- First Prompt: Say: "I have uploaded my existing project. Based on the System Instructions, let's start by architecting the Lambda function that uses LiteLLM to connect to my Claude Opus 4.6 API."

**What it does well:**  
- It introduces an AI/LLM integration layer to the portfolio, which is a genuinely new dimension. 
- The serverless Lambda angle adds compute variety beyond Fargate and EC2. 
- It builds naturally on the established "Dark VPC" pattern.


### 1.2 Claude Opus 4.6's take on the project listed above
**Concerns:**
The core problem is demonstrability.  
A "self-healing agent" needs real incidents to heal.  
In a personal project with no production traffic, it is possible to either be simulating failures (which feels contrived to an interviewer) or the agent just sits idle.  
Compare that to the Tennis Masters Tour project, which showed a live failover on a real domain with real data — that was convincing because the scenario was genuine.  

There's also significant overlap:  
- Previous projects already demonstrated `Terraform`, `VPC Endpoints`, the `Dark VPC` pattern, and `Secrets Manager`. 
- The new surface area is really just the LLM orchestration piece, which risks looking like a wrapper around API calls.  
- The multi-model `LiteLLM` + `Claude` + `Gemini` setup adds architectural complexity that's hard to justify.  
- An interviewer will ask "why two models?" and the honest answer is that for a project this size, one would suffice. It can come across as résumé-driven architecture.

What the portfolio actually lacks after these two projects:
- CI/CD (no GitHub Actions or CodePipeline yet)
- observability beyond CloudWatch alarms
- any NoSQL or DynamoDB work
- Step Functions or workflow orchestration
- EKS/Kubernetes could be a direction worth pursuing.


### 1.3 Other project idea: migrating my ITF project from Fargate to Kubernetes? Is an agentic project not worth more for my portfolio?
**Kubernetes:**
The Kubernetes migration is safe and solid.  
EKS is in high demand, and migrating a real app (not a hello-world) from Fargate to Kubernetes is a legitimate project.  
It would mean learning Helm charts, manifests, ingress controllers, and the EKS networking model.  
But it's fundamentally a re-platform of something already built in the last project.  
The architecture diagram looks almost identical, just with a different compute layer. Interviewers might see it as "same project, different runtime."

**Agreement with Gemini:**  
The job market is shifting. Agentic AI is not a buzzword anymore — it's showing up in real job descriptions.  
Having a project that proves you can wire LLMs into infrastructure workflows is increasingly valuable.  
Very few candidates have that on their portfolio right now. That scarcity matters.

**Disagreement with Gemini:**  
The specific design it proposed is overengineered for a portfolio project and trying too many things:
- Two LLM providers
- `LiteLLM` abstraction
- self-healing against simulated failures  



## 2. New Project idea: agentic project
**The middle path:**  
Take the agentic concept but make it narrowly scoped and demonstrable.  
For example, an agent that:
- watches `AWS Config` drift events.
- summarizes incidents using a single `LLM` (Claude via Bedrock, keeping everything inside AWS)
- generates a Terraform plan as a pull request on GitHub.  

That would be one model, not two:
- Bedrock instead of raw API keys, a service not demonstrated yet. 
- GitHub Actions to close the CI/CD gap. 
- And the output is a concrete artifact — a PR with a diff — that can be screenshot and shown.

That would give the "agentic" story Gemini is right about, without the demonstrability and over-engineering problems.



## 3. Why Bedrock?
This is actually a critical point for this project design.  
A paid Claude subscription enhances the chat experience but doesn't include access to the Claude API or Console.  
The Claude Max subscription covers claude.ai and Claude Code in the terminal, but it cannot be used to make API calls from a Lambda function.  

So the choice for this agentic project is really between three options:
- Anthropic API (pay-per-token): one needs a separate Console account with credits. For a demo with maybe a few hundred calls, we're probably talking $2–5 total. 
    - The upside is we can get the exact model we want (Opus 4.6). 
    - The downside is it adds zero new AWS services to my portfolio — it's just an HTTP call with a key in `Secrets Manager`.

- AWS Bedrock: Similar per-token cost, possibly slightly more. 
    But it adds a meaningful new AWS service to the story. We access Claude through AWS, which means:
        - IAM roles instead of API keys
        - native CloudWatch metrics on the LLM calls
        - no `Secrets Manager` needed for the AI piece since authentication is handled by the execution role. 
    That's a cleaner architecture and a better résumé line.

- Gemini Pro: Zero cost for now. But no new AWS service, and it weakens the "all-in on AWS" narrative my portfolio currently tells.

The bottom line: 
- the Max subscription doesn't factor into this decision at all — none of these approaches can use it. 
- Given that the cost difference between Anthropic API and Bedrock is negligible for a demo, Bedrock gives more portfolio value per dollar. 
- This is already costing a few dollars on Lambda, CloudWatch, and whatever else the agent touches — adding Bedrock to that is marginal cost for meaningful signal.

**Decision:**
- If zero cost on the AI layer is a hard requirement, it is better to use Gemini's free API tier via AI Studio's free tier. It works, it's genuinely free, and the agent will function.  
    The tradeoff is that the architecture diagram says "Google AI Studio" in the middle of an otherwise all-AWS project, which is a bit awkward but defensible.
- For a few more dollars (likely spend less than $5 on the LLM calls for a demo-scale project), Bedrock is the stronger move for the reasons I outlined:
    - IAM-native auth
    - no API keys to manage
    - new AWS service on the résumé
    - and it keeps the entire architecture inside AWS. 

The recommendation hasn't changed: 
- Bedrock gives the most portfolio value for a trivial cost. 
- if budget is truly zero, Gemini's free API tier is a legitimate path. The existing Gemini Pro subscription doesn't help either way though.



## 4. Preparing the project on Claude Max
**Claude Max (development phase):**  
That's the development tool. It is already paid for, and it's the best coding assistant to have access to, the same way it is used right now:
- talking through architecture
- generating code
- debugging Terraform
- writing Python

**Bedrock (runtime, inside the project):**  
This is what the Lambda function calls when it needs to reason about a `AWS Config` drift event or generate a Terraform plan.  
It's a component inside the architecture, not the development environment.  
They don't overlap at all. It's like using PyCharm to write code that calls an AWS service, they're different layers.  

So the cost structure would be:
- Development: $0 incremental (existing Max subscription)
- Bedrock runtime for demo: a few dollars at most
- Infrastructure (Lambda, CloudWatch, etc.): pennies
- Total new spend: probably under $5

And the architecture diagram gets to show:
Lambda → Bedrock → Claude (with IAM role auth, no API keys), which is clean and all-AWS.  
That's a much stronger story than Lambda → Secrets Manager → external API.



## 5. What can run locally
The core agent logic is just Python, in order to write the function that:  
- takes an `AWS Config` drift events
- sends it to an LLM
- gets back a Terraform plan.

Locally, it is possible to call Claude manually using Sonnet 4.5 or Opus 4.6:
- paste a simulated `AWS Config` drift event JSON into claude.ai or Claude Code
- iterate on the prompt
- refine the output format.  

Once the prompt engineering is solid, one can swap the call to Bedrock in the Lambda version.  
The reasoning logic is identical, only the transport changes.

Terraform plan generation and validation is entirely local too:
- `terraform init`
- `terraform plan`
- `terraform validate`  

All are free, no AWS needed. 
The agent 
- generates an HCL file
- I run terraform plan to verify it's valid. 

That's the core feedback loop.

One could also simulate the full pipeline locally, the entire chain working on a laptop at zero cost:
- write a Python script
- this script reads a fake `AWS Config` drift event from a JSON file
- it passes it to Claude (via Claude Code's -p flag for programmatic output)
- it gets a suggested fix,
- it writes a `.tf` file
- it runs `terraform validate`. 

**What requires AWS:**
- The actual `AWS Config` drift events triggering the Lambda
- the Bedrock integration
- IAM roles
- the EventBridge wiring. 

That would happen on deployment day — the same 1-2 day window used for the DR project.
Therefore, the workflow would be: 
- develop and test locally for days 
- → deploy to AWS for screenshots and demo 
- → tear it down. 

That would be the same playbook as for the Tennis project which ended up at a cost of around $8.



## 6. Orchestration and CI/CD
### 6.1 Step Functions  
The agent lifecycle will be a Step Functions workflow rather than a single monolithic Lambda. These are the various steps, in order:
- receive drift event
- query DynamoDB history
- call Bedrock
- generate Terraform
- validate
- apply or escalate

Each step becomes a discrete state with error handling and retry logic.  
The visual workflow diagram Step Functions provides is also a strong demo artifact.


### 6.2 GitHub Actions  
This is a pipeline that runs `terraform validate` and `terraform plan` on the agent's proposed fixes before they're applied.  
This closes the `CI/CD` gap and makes the output auditable.  



## 7. Using a DynamoDB database
First, the key is that it has to feel natural, not bolted on. Here are a few uses that would actually make sense in an agentic SRE project:

### 7.1 Incident logging
Every time the agent triggers, the event is stored: 
- timestamp
- drift event type
- what the agent diagnosed
- what Terraform fix it proposed
- whether it was applied or rejected. 

That's a legitimate operational audit trail.  
The schema is naturally semi-structured (different alarm types produce different payloads), which is exactly where DynamoDB fits better than PostgreSQL.  
An interviewer asking "why DynamoDB here?" gets a clean answer.


### 7.2 Agent decision history for context
When a new drift event arrives, the agent queries DynamoDB to check: 
- "have I seen this before? 
- What did I do last time? 
- Did the fix work?" 

That turns the agent from stateless to stateful, which is a significant upgrade in sophistication.  
- The LLM prompt becomes "here's the current alarm AND here are the last 3 times this happened" — that's a genuinely better architecture, not a résumé-padding exercise.


### 7.3 Terraform state metadata — not the state file itself (that stays in `S3`), but a record of what changes the agent has proposed and applied: 
- which resources were modified
- when
- before/after diff. 

This is useful for a dashboard or rollback decisions.

The first two (incident log / agent decision history for context) are the strongest. Together they give a DynamoDB table with:
- a partition key of `drift_type` 
- a sort key of `timestamp`
- maybe a GSI on `status` to query unresolved incidents. 

Simple, clean, and justified.

And yes — now DataGrip earns a seat at the table, since it supports DynamoDB browsing. 
It can be used to inspect the incident log during development.



## 8. Why DynamoDB Over PostgreSQL for Incident Tracking
### 8.1 The Problem  
An Agentic SRE system processes alerts from multiple AWS sources: 
- security group rule added
- S3 bucket policy changed
- IAM role permissions modified
- EC2 instance tag removed
- and more. 

The system must track each incident through its full lifecycle: 
- the initial alert
- the agent's diagnosis and decision
- the Terraform fix that was proposed and whether it was applied.

Each alert type carries a different set of fields.
A CPU alarm includes:
- `threshold`
- `average_cpu`
- `instance_id`.  

A health check failure includes:
- `endpoint`
- `status_code`
- `region`.  

A disk space alert includes:
- `volume_id`
- `percent_used`.

The incident log must store all of these — along with the agent's diagnosis, the proposed Terraform fix, and the outcome — in a single table.

### 8.2 Why PostgreSQL Is a Poor Fit

PostgreSQL requires a fixed schema. To accommodate every possible alert type, two approaches exist, and both are problematic.

**Wide table approach:** A single table with every possible column from every alert type. Most rows would have the majority of columns set to NULL. The table becomes difficult to read, wasteful in storage, and fragile — every new alert type requires an `ALTER TABLE` migration.

**Multiple tables approach:** One table per alert type (e.g., `cpu_incidents`, `healthcheck_incidents`, `disk_incidents`). Querying across all incident types then requires `UNION ALL` across every table. Adding a new alert type means creating an entirely new table.

Neither approach handles the fundamental reality: incident data is **semi-structured by nature**.

### 8.3 Why DynamoDB Fits Naturally

DynamoDB is schema-flexible at the item level. Every item shares the same key structure, but the remaining attributes can vary freely.

**Key design:**

| Key        | Field          | Purpose                              |
|------------|----------------|--------------------------------------|
| Partition  | `drift_type`   | Groups incidents by category         |
| Sort       | `timestamp`    | Orders incidents chronologically     |

**Flexible attributes:**  
Each item includes only the fields relevant to that drift type.  
A security group drift incident stores:
- `rule_id`
- `port_range`
- `cidr_block`.

An S3 public access drift incident stores:
- `bucket_name`
- `block_public_acls`
- `previous_setting`.
No NULLs, no wasted columns, no migrations when a new drift type is introduced.

**Common fields**  
For example:
- `agent_diagnosis`
- `proposed_fix`
- `fix_applied`
- `resolution_status` 
They appear on every item, regardless of alarm type.

**Lifecycle updates:**  
Each item is written once when the alert arrives, then updated as the agent progresses.  
The diagnosis, proposed Terraform fix, and resolution outcome are added to the same item over time.  
Since DynamoDB attributes are flexible, these later fields do not need to exist at creation time — they are simply added on update.  
This means a single table and a single item per incident covers the full lifecycle:  
- logging
- decision history
- Terraform change tracking.

**Global Secondary Index (GSI):**  
An index on `resolution_status` allows efficient queries for unresolved incidents across all drift types — without scanning the entire table.

### 8.4 Summary

| Criteria                                          | PostgreSQL                      | DynamoDB                          |
|---------------------------------------------------|---------------------------------|-----------------------------------|
| Schema flexibility (per item and over life cycle) | Fixed; requires migrations      | Flexible per item                 |
| Handling varied drift types                       | Wide table or many tables       | Single table, varied attributes   |
| Adding new alert types                            | ALTER TABLE or new table        | No schema change needed           |
| Querying across all types                         | UNION ALL or NULLs              | Single query on partition key     |
| Operational overhead                              | RDS instance management         | Fully serverless, pay-per-request |
| Cost when idle                                    | RDS runs 24/7 unless stopped    | Zero cost at rest (on-demand mode)|

DynamoDB is the right choice because:
- the data is semi-structured
- the access patterns are simple (write on alert, read by type or status)
- the serverless pricing model aligns with an ephemeral, cost-conscious project.



## 9. Tools used
And yes — now DataGrip earns a seat at the table, since it supports DynamoDB browsing. 
It can be used to inspect the incident log during development.

PyCharm with DynamoDB — yes, it gains more relevance.  
- Beyond the Terraform HCL plugin, PyCharm's debugger becomes valuable for stepping through the agent's DynamoDB queries:
    - inspecting what the boto3 call returns
    - verifying the incident history is structured correctly. 
- The AWS Toolkit plugin for PyCharm also provides a DynamoDB table browser directly in the IDE, similar to what DataGrip offers. 
- And for the Python side, PyCharm's type hints and autocomplete on boto3 resource/client objects are genuinely helpful — the DynamoDB API is verbose and easy to get wrong. 

All of that is documentable in a README.



## 10. Project duration
The local development phase could be days, not weeks.  
The Tennis project took about three weeks total, but that had:
- 24 tables
- 30+ scripts
- 20 routes.

Here we have an agent with:
- a few Lambda functions
- one DynamoDB table
- prompt logic
- a Step Functions workflow
- a GitHub Actions pipeline

This is a much smaller surface.  
A realistic timeline might be:
- a few days of local development
- 1–2 days on AWS for deployment and screenshots



