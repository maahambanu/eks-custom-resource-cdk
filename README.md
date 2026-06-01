# Platform Engineering Assignment
 
This project demonstrates a platform engineering solution built with AWS CDK (Python).
 
The solution provisions:
 
* Amazon EKS Cluster
* AWS Systems Manager Parameter Store
* Lambda-backed Custom Resource
* ingress-nginx Helm Chart
* CloudWatch Monitoring and Alarms
The purpose of the assignment is to dynamically generate Helm values based on the deployment environment (`development`, `staging`, or `production`) using a Lambda-backed Custom Resource.
 
---
 
## Architecture
 
```text
SSM Parameter Store
(/platform/account/env)
          │
          ▼
Lambda-backed Custom Resource
          │
          ▼
Generated Helm Values
          │
          ▼
ingress-nginx Helm Chart
          │
          ▼
Amazon EKS
```
 
---
 
## Environment Behaviour
 
| Environment | Replica Count |
| ----------- | ------------- |
| Development | 1             |
| Staging     | 2             |
| Production  | 2             |
 
The Lambda function retrieves the environment value from Parameter Store and dynamically generates the Helm values consumed by the ingress-nginx Helm chart.
 
---
## Multi-Account Strategy

This solution is designed for a multi-account AWS setup:

| Account | Purpose | Environments |
|---------|---------|--------------|
| Non-Production (swisscom-nonprod) | Development and staging workloads | development, staging |
| Production (swisscom-prod) | Production workloads only | production |

The same CDK code deploys to both accounts. Environment
behaviour is driven entirely by the SSM parameter value
pre-configured in each account, the code never changes
between accounts.

In a real Swisscom setup this parameter would be set
automatically during account vending. Here it is created
as part of the stack to simulate that pattern.
 
## Project Structure
 
```text
.
├── app.py
├── cdk.json
├── requirements.txt
├── lambda
│   └── handler.py
├── tests
│   └── unit
│       └── test_helm_config.py
└── eks_custom_resource_cdk
    └── platform_stack.py
```
 
---
 
## Prerequisites
 
* Python 3.12+
* AWS CLI
* AWS CDK v2
* kubectl
* AWS Account
---
 
## Setup
 
Create a virtual environment:
 
```bash
python -m venv .venv
```
 
Activate the virtual environment:
 
**Linux / MacOS**
 
```bash
source .venv/bin/activate
```
 
**Windows**
 
```powershell
.venv\Scripts\Activate.ps1
```
 
Install dependencies:
 
```bash
pip install -r requirements.txt
```
 
Verify CDK installation:
 
```bash
cdk --version
```
 
---
 
## Running Unit Tests
 
Run the Lambda unit tests:
 
```bash
python -m pytest -v
```
 
Example output:
 
```text
5 passed
```
 <img width="941" height="224" alt="test results" src="https://github.com/user-attachments/assets/dc4667c0-9336-45f1-afc0-eddeaad7c817" />

---
 
## Deployment
 
### Development
 
```bash
cdk deploy \
-c env=development \
-c account=<nonprod-account-id> \
-c region=eu-west-1 \
--profile swisscom-nonprod
```
<img width="640" height="97" alt="describe stack" src="https://github.com/user-attachments/assets/3e4d3e59-694c-4cc6-9fea-c665de20b0c1" />
<img width="950" height="224" alt="Screenshot 2026-05-31 123300" src="https://github.com/user-attachments/assets/9dd7126b-1b0e-4aa4-a800-d6b1e05a4027" />


Expected result:
 
```text
controller.replicaCount = 1
```
 <img width="911" height="59" alt="dev-replica" src="https://github.com/user-attachments/assets/ecd74875-1b56-44cc-9e4a-6d665a2335ee" />

### Staging
 
```bash
cdk deploy \
-c env=staging \
-c account=<nonprod-account-id> \
-c region=eu-west-1 \
--profile swisscom-nonprod
```
 
Expected result:
 
```text
controller.replicaCount = 2
```
<img width="814" height="119" alt="pods" src="https://github.com/user-attachments/assets/b8881a66-a910-496b-aef6-36cc9b21444f" />

 
### Production
 
```bash
cdk deploy \
-c env=production \
-c account=<prod-account-id> \
-c region=eu-west-1 \
--profile swisscom-prod
```
 
Expected result:
 
```text
controller.replicaCount = 2
```
 
---
 
## Verification
 
Verify the SSM Parameter:
 
```bash
aws ssm get-parameter \
--name /platform/account/env
```
 
Verify the EKS cluster:
 
```bash
kubectl get nodes
```
 
Verify ingress-nginx deployment:
 
```bash
kubectl get deployment ingress-nginx-controller -n ingress-nginx
```
 
Verify ingress-nginx pods:
 
```bash
kubectl get pods -n ingress-nginx
```
 <img width="538" height="94" alt="SSM parameter" src="https://github.com/user-attachments/assets/85e6bcbb-ad1f-4a42-ae32-d1b838be0b1d" />

---
 
## Monitoring
 
The platform provisions CloudWatch alarms for:
 
* Lambda Errors
* Lambda Duration
The Lambda function also emits structured logs to CloudWatch for:
 
* Environment resolution
* Parameter retrieval
* Helm value generation
* Custom Resource lifecycle events
<img width="950" height="394" alt="lambda tail logs" src="https://github.com/user-attachments/assets/8ca6843a-8d93-493a-b3e5-c483defacfa3" />
<img width="743" height="235" alt="Lambda cloudwatch events" src="https://github.com/user-attachments/assets/64ea746e-26b9-491f-9033-38ec13dad642" />
<img width="946" height="442" alt="log groups" src="https://github.com/user-attachments/assets/20987f7a-df39-47b9-928c-364ead4076cd" />
<img width="939" height="299" alt="Logstreams" src="https://github.com/user-attachments/assets/ccc657d9-f10d-4336-b76e-24f242022e7d" />

---
 
## Security
 
The solution implements:
 
* Principle of Least Privilege for Lambda permissions
* Parameter Store access restrictions
* EKS Access Entries
* EKS Access Policies
* Separate AWS accounts for Production and Non-Production workloads

### Network Isolation

The EKS cluster is deployed inside a dedicated VPC.

Benefits include:

- Network segmentation
- Security Groups
- Private Subnets
- Controlled outbound internet access through NAT Gateway
- Separation from other workloads

#### Least Privilege
__Example 1: Least Privilege for SSM__

```
env_parameter.grant_read(helm_config_function)
```
Lambda can:
✓ Read exactly one parameter

Lambda cannot:
✗ Create parameters
✗ Delete parameters
✗ Read all parameters
✗ Access Secrets Manager
✗ Access other AWS services

__Example 2: Lambda doesn't have admin permissions__

```
GetParameter
```
It does not need:
```
eks:*
ec2:*
iam:*
cloudformation:*
```
__Example 3: Dedicated SSM Parameter__
Instead of:
```
/platform/*
```
I used:
```
/platform/account/env
```
To prevent Lambda from reading every platform parameter.

__Example 4: EKS Access Policies__
We granted only to the principal that is required:
```
aws eks create-access-entry
aws eks associate-access-policy
AmazonEKSClusterAdminPolicy
```


---

 
## Design Decisions
 
### Why Parameter Store?
 
Parameter Store provides centralized environment configuration and allows the Lambda-backed Custom Resource to dynamically determine deployment behaviour.
 
### Why a Lambda-backed Custom Resource?
 
The assignment requires Helm values to be generated dynamically at deployment time rather than being hardcoded into the CDK stack.
 
### Why Helm?
 
Helm provides a standard mechanism for packaging and deploying Kubernetes applications.
 
### Why ingress-nginx?
 
ingress-nginx is a commonly used ingress controller and serves as a realistic platform component for demonstrating environment-specific configuration.
 
### Why Configuration Was Isolated from Infrastructure

The platform was designed with a clear separation of concerns between infrastructure provisioning, configuration management, and application deployment.

AWS CDK is responsible for provisioning infrastructure resources such as networking, EKS, IAM, Lambda, and monitoring. Environment-specific behaviour is externalized through configuration and Parameter Store rather than being embedded directly in the infrastructure code. This enables the same stack to be deployed consistently across multiple environments while allowing environment-specific customization.

This approach provides several benefits:

- Reusable infrastructure code
- Reduced duplication across environments
- Easier operational management
- Improved maintainability
- Lower risk of configuration drift
- Better alignment with platform engineering best practices

The Lambda-backed Custom Resource further reinforces this pattern by dynamically generating Helm configuration at deployment time, allowing Kubernetes deployments to adapt to the target environment without modifying the underlying infrastructure definitions.
 
---
 
## Useful Commands
 
List stacks:
 
```bash
cdk ls
```
 
Synthesize CloudFormation template:
 
```bash
cdk synth
```
 
Deploy stack:
 
```bash
cdk deploy
```
 
Compare deployed infrastructure with local changes:
 
```bash
cdk diff
```
 
Destroy stack:
 
```bash
cdk destroy
```
 
---

 
## Author
 
**Maaham Banu**
 
Platform Engineering Assignment Submission
 
AWS CDK | Amazon EKS | Lambda | Helm | Systems Manager | CloudWatch
