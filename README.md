# MLOps Pipeline with AWS CDK

Serverless MLOps regression pipeline: upload a CSV → XGBoost trains → model deploys → prediction tested → endpoint cleaned up automatically.

---

## Table of Contents

1. [What This Does](#what-this-does)
2. [Prerequisites](#prerequisites)
3. [Step 1 — AWS Account Setup](#step-1--aws-account-setup)
4. [Step 2 — Install Required Tools](#step-2--install-required-tools)
5. [Step 3 — Configure AWS CLI](#step-3--configure-aws-cli)
6. [Step 4 — Clone / Open the Project](#step-4--clone--open-the-project)
7. [Step 5 — Set Up Python Environment](#step-5--set-up-python-environment)
8. [Step 6 — Bootstrap CDK](#step-6--bootstrap-cdk)
9. [Step 7 — Deploy the Stack](#step-7--deploy-the-stack)
10. [Step 8 — Test the Pipeline](#step-8--test-the-pipeline)
11. [Step 9 — Monitor on AWS Console](#step-9--monitor-on-aws-console)
12. [Step 10 — Clean Up](#step-10--clean-up)
13. [Troubleshooting](#troubleshooting)

---

## What This Does

When you upload a `.csv` file to the S3 bucket's `train/` folder:

```
Upload CSV  →  S3 Event  →  Lambda (Trigger)  →  Step Functions
    →  SageMaker XGBoost Training  →  Create Model
    →  Create Endpoint  →  Lambda (Test prediction)
    →  Lambda (Delete endpoint to avoid costs)
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | ≥ 3.7 | CDK stack code + Lambda functions |
| Node.js + npm | ≥ 14 | CDK CLI runs on Node |
| AWS CLI | Latest | Talk to AWS from terminal |
| AWS CDK CLI | Latest | Deploy infrastructure |

---

## Step 1 — AWS Account Setup

### 1.1 Create a Free AWS Account
1. Go to [https://aws.amazon.com/](https://aws.amazon.com/)
2. Click **Create a Free Account**
3. Follow sign-up steps (credit card required, but Free Tier is sufficient)

### 1.2 Create an IAM User (do NOT use root account)
1. Log in to **AWS Console** → search for **IAM**
2. Click **Users** → **Create user**
3. Username: `cdk-deploy-user`
4. Click **Next** → **Attach policies directly**
5. Attach these policies:
   - `AdministratorAccess` *(for learning/assignment use)*
6. Click **Create user**
7. Click the newly created user → **Security credentials** tab
8. Scroll to **Access keys** → **Create access key**
9. Choose **Command Line Interface (CLI)**
10. Click **Next** → **Create access key**
11. **IMPORTANT:** Copy/download the `Access Key ID` and `Secret Access Key` — you won't see the secret again

---

## Step 2 — Install Required Tools

### 2.1 Install Node.js
Download from [https://nodejs.org/](https://nodejs.org/) (LTS version)

Verify:
```bash
node -v
npm -v
```

### 2.2 Install AWS CDK CLI
```bash
npm install -g aws-cdk
```

Verify:
```bash
cdk --version
```

### 2.3 Install AWS CLI
- Windows: Download installer from [https://aws.amazon.com/cli/](https://aws.amazon.com/cli/)
- Or via pip:
```bash
pip install awscli
```

Verify:
```bash
aws --version
```

### 2.4 Install Python (if not already installed)
Download from [https://python.org/](https://python.org/) (3.9 recommended)

---

## Step 3 — Configure AWS CLI

Open your terminal and run:

```bash
aws configure
```

Enter the values when prompted:
```
AWS Access Key ID [None]:     PASTE_YOUR_ACCESS_KEY_ID
AWS Secret Access Key [None]: PASTE_YOUR_SECRET_ACCESS_KEY
Default region name [None]:   us-east-1
Default output format [None]: json
```

Verify it works:
```bash
aws sts get-caller-identity
```

You should see your account ID and user ARN printed.

---

## Step 4 — Clone / Open the Project

The project is already at:
```
Task2/mlops-cdk-pipeline/
```

Navigate into it in your terminal:
```bash
cd "d:\Hashir\8th_semester\Cloud\Assignments\Task2\mlops-cdk-pipeline"
```

---

## Step 5 — Set Up Python Environment

### 5.1 Create a virtual environment
```bash
python -m venv .venv
```

### 5.2 Activate it

**Windows (Command Prompt / PowerShell):**
```bash
.venv\Scripts\activate
```

**Mac / Linux:**
```bash
source .venv/bin/activate
```

You'll see `(.venv)` at the start of your terminal prompt — this means it's active.

### 5.3 Install dependencies
```bash
pip install -r requirements.txt
```

This installs `aws-cdk-lib`, `constructs`, and `boto3`.

### 5.4 Verify CDK can see the app
```bash
cdk synth
```

This should print a CloudFormation template (long JSON/YAML output). No errors = good.

---

## Step 6 — Bootstrap CDK

> **This only needs to be done ONCE per AWS account per region.**

```bash
cdk bootstrap
```

This creates an S3 bucket and ECR repo in your AWS account that CDK uses to stage assets during deployment. Takes about 1–2 minutes.

Expected output:
```
✅  Environment aws://YOUR_ACCOUNT_ID/us-east-1 bootstrapped.
```

---

## Step 7 — Deploy the Stack

```bash
cdk deploy
```

CDK will show you what it's about to create and ask for confirmation:
```
Do you wish to deploy these changes (y/n)? y
```

Type `y` and press Enter. Deployment takes **3–5 minutes**.

When done, you'll see output like:
```
Outputs:
MLOpsStack.BucketName      = mlopsstack-datasetbucket-abc123
MLOpsStack.StateMachineArn = arn:aws:states:us-east-1:123456789:stateMachine/MLOpsStateMachine
```

**Copy the `BucketName` value — you'll need it in the next step.**

---

## Step 8 — Test the Pipeline

### 8.1 Prepare a sample CSV file

Create a file called `sample.csv` in a `train/` folder with some numeric regression data, for example:
```
feature1,feature2,feature3,label
0.5,0.3,0.1,1.2
0.8,0.6,0.2,2.1
0.2,0.1,0.9,0.8
```

### 8.2 Upload the CSV to S3

Replace `YOUR_BUCKET_NAME` with the bucket name from Step 7:

```bash
aws s3 cp train/ s3://YOUR_BUCKET_NAME/train/ --recursive
```

Or upload a single file:
```bash
aws s3 cp sample.csv s3://YOUR_BUCKET_NAME/train/sample.csv
```

This upload **automatically triggers the pipeline**.

---

## Step 9 — Monitor on AWS Console

### 9.1 Watch Step Functions
1. Go to [https://console.aws.amazon.com/states/](https://console.aws.amazon.com/states/)
2. Make sure region is **us-east-1** (top-right dropdown)
3. Click **MLOpsStateMachine**
4. Click the latest execution
5. You'll see each step turn green as it completes:
   - ✅ TrainXGBoost
   - ✅ CreateModel
   - ✅ CreateEndpointConfig
   - ✅ CreateEndpoint
   - ✅ TestEndpoint
   - ✅ DeleteEndpoint

### 9.2 Watch SageMaker Training
1. Go to [https://console.aws.amazon.com/sagemaker/](https://console.aws.amazon.com/sagemaker/)
2. Click **Training jobs** in the left sidebar
3. You'll see a job running → then **Completed**

### 9.3 Check Lambda Logs
1. Go to **CloudWatch** → **Log groups**
2. Search for `/aws/lambda/MLOpsStack`
3. Click the log group for `TestLambda` to see the prediction output

---

## Step 10 — Clean Up

When you're done, **delete all AWS resources** to avoid any charges:

```bash
cdk destroy
```

Type `y` when prompted. This deletes:
- The S3 bucket and all its contents
- All Lambda functions
- The Step Functions state machine
- All IAM roles

> ⚠️ The SageMaker endpoint is automatically cleaned up *by the pipeline itself* (the `delete.py` Lambda). But always verify in the SageMaker console that no endpoints are running.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `cdk: command not found` | Run `npm install -g aws-cdk` again |
| `Unable to locate credentials` | Run `aws configure` and enter your keys |
| `CDK bootstrap required` | Run `cdk bootstrap` first |
| `cdk synth` shows import errors | Make sure `.venv` is active and `pip install -r requirements.txt` ran |
| S3 upload works but pipeline doesn't trigger | Check that file is in the `train/` prefix, not root of bucket |
| SageMaker training fails | Check CloudWatch logs under `/aws/sagemaker/TrainingJobs` |
| `cdk destroy` fails on S3 bucket | S3 bucket has `auto_delete_objects=True` so it should work; retry once |
