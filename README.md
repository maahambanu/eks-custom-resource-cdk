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
 
Expected result:
 
```text
controller.replicaCount = 1
```
 
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
---
 
## Security
 
The solution implements:
 
* Principle of Least Privilege for Lambda permissions
* Parameter Store access restrictions
* EKS Access Entries
* EKS Access Policies
* Separate AWS accounts for Production and Non-Production workloads
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
 
### Why AWS CDK?
 
AWS CDK enables Infrastructure as Code using Python while maintaining CloudFormation compatibility and repeatability.
 
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
