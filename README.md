# MLOps Pipeline with AWS CDK

This repository contains a serverless MLOps regression pipeline built using AWS CDK (Cloud Development Kit). It demonstrates how to automate the training, deployment, testing, and cleanup of an XGBoost model on AWS SageMaker.

The pipeline is triggered automatically when a CSV dataset is uploaded to an S3 bucket.

---

## 🚀 Features

- **Infrastructure as Code (IaC):** Entire infrastructure defined in Python using AWS CDK.
- **Serverless Workflow:** Orchestrated by AWS Step Functions.
- **Automated Training:** Uses SageMaker to train an XGBoost model.
- **Auto-Deployment:** Deploys the trained model to a SageMaker endpoint.
- **Automated Testing:** A Lambda function tests the endpoint with sample data.
- **Cost Optimization:** Automatically deletes the costly SageMaker endpoint after testing.

---

## 🏗 Architecture

1. **User** uploads a `train/*.csv` file to an S3 Bucket.
2. **S3 Event Notification** triggers a Lambda function.
3. **Lambda** starts a **Step Functions** state machine.
4. **Step Functions** orchestrates the workflow:
    - **Train:** Starts a SageMaker Training Job (XGBoost).
    - **Create Model:** Creates a SageMaker Model resource.
    - **Configure Endpoint:** Creates an Endpoint Configuration.
    - **Deploy:** Deploys the Model to a real-time Endpoint.
    - **Test:** Invokes a Lambda to send sample data to the Endpoint.
    - **Cleanup:** Invokes a Lambda to delete the Endpoint and Config (saving costs).

---

## 📂 Project Structure

```
mlops-cdk-pipeline/
├── app.py                 # CDK App entry point
├── cdk.json               # CDK configuration
├── requirements.txt       # Python dependencies
├── stacks/
│   └── mlops_stack.py     # Definition of the Main CDK Stack (S3, SageMaker, Step Functions)
├── lambda/
│   ├── index.py           # Trigger Lambda (starts Step Functions)
│   ├── test.py            # Test Lambda (invokes SageMaker Endpoint)
│   └── delete.py          # Cleanup Lambda (deletes Endpoint)
└── README.md              # Detailed local setup guide
```

---

## 🛠 Prerequisites

Before you begin, ensure you have the following installed:

1.  **AWS Account:** With `AdministratorAccess` (or sufficient permissions for files, SageMaker, IAM, Lambda, etc.).
2.  **AWS CLI:** configured with your credentials (`aws configure`).
3.  **Node.js & npm:** Required for the CDK CLI.
4.  **Python 3.9+:** For the infrastructure code and Lambda functions.
5.  **AWS CDK CLI:** Install via `npm install -g aws-cdk`.

---

## 📥 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/RanaHashir0/mlops-cdk-pipeline.git
    cd mlops-cdk-pipeline
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # Mac/Linux:
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🚀 Deployment

1.  **Bootstrap CDK (One-time setup per region):**
    ```bash
    cdk bootstrap
    ```

2.  **Synthesize the template (Optional check):**
    ```bash
    cdk synth
    ```

3.  **Deploy the stack:**
    ```bash
    cdk deploy
    ```
    *Confirm strictly by typing `y` when prompted.*

    **Note:** After deployment, note down the **Bucket Name** from the outputs.

---

## 🧪 Usage / Testing

1.  **Prepare a Dataset:**
    Create a file named `sample.csv` (or use the one provided in `train/` if available).

2.  **Upload to S3:**
    Upload the file to the `train/` folder in your new S3 bucket.
    ```bash
    aws s3 cp train/sample.csv s3://YOUR_BUCKET_NAME/train/sample.csv
    ```

3.  **Watch it Run:**
    - Go to the **AWS Step Functions** console.
    - Select the `MLOpsStateMachine`.
    - You should see a new execution running.
    - Follow the steps turn green as it trains, deploys, tests, and cleans up!

---

## 🧹 Cleanup

To remove all resources and avoid future charges:

```bash
cdk destroy
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1.  Fork the project.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
