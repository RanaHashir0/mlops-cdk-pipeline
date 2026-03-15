from aws_cdk import (
    Stack, aws_s3 as s3, aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_iam as iam, aws_s3_notifications as s3n,
    aws_ec2 as ec2,
    RemovalPolicy, Duration, Size, CfnOutput
)
from constructs import Construct
import os

XGBOOST_IMAGE = '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1'

class MLOpsStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # S3 Bucket for dataset
        bucket = s3.Bucket(self, 'DatasetBucket',
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True)

        # IAM Role — allows SageMaker to access S3 + CloudWatch
        sagemaker_role = iam.Role(self, 'SageMakerExecutionRole',
            assumed_by=iam.ServicePrincipal('sagemaker.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchLogsFullAccess')
            ])

        # Test Lambda
        test_lambda = lambda_.Function(self, 'TestLambda',
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler='test.handler',
            code=lambda_.Code.from_asset(os.path.join(os.getcwd(), 'lambda')))
        test_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=['sagemaker:InvokeEndpoint'],
            resources=['*']))

        # Cleanup Lambda
        delete_lambda = lambda_.Function(self, 'DeleteLambda',
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler='delete.handler',
            code=lambda_.Code.from_asset(os.path.join(os.getcwd(), 'lambda')))
        delete_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                'sagemaker:DeleteEndpoint',
                'sagemaker:DeleteEndpointConfig',
                'sagemaker:DeleteModel'
            ],
            resources=['*']))

        # Step 1: SageMaker Training Job
        training_step = tasks.SageMakerCreateTrainingJob(
            self, 'TrainXGBoost',
            integration_pattern=sfn.IntegrationPattern.RUN_JOB,
            training_job_name=sfn.JsonPath.string_at('$$.Execution.Name'),
            algorithm_specification=tasks.AlgorithmSpecification(
                training_image=tasks.DockerImage.from_registry(XGBOOST_IMAGE),
                training_input_mode=tasks.InputMode.FILE
            ),
            hyperparameters={
                "num_round": "10"
            },
            input_data_config=[tasks.Channel(
                channel_name='train',
                content_type='text/csv',
                data_source=tasks.DataSource(
                    s3_data_source=tasks.S3DataSource(
                        s3_location=tasks.S3Location.from_bucket(bucket, 'train/'),
                        s3_data_type=tasks.S3DataType.S3_PREFIX,
                        s3_data_distribution_type=tasks.S3DataDistributionType.FULLY_REPLICATED
                    )))],
            output_data_config=tasks.OutputDataConfig(
                s3_output_location=tasks.S3Location.from_bucket(bucket, 'output/')),
            resource_config=tasks.ResourceConfig(
                instance_count=1,
                instance_type=ec2.InstanceType.of(ec2.InstanceClass.M4, ec2.InstanceSize.XLARGE),
                volume_size=Size.gibibytes(30)),
            role=sagemaker_role,
            stopping_condition=tasks.StoppingCondition(
                max_runtime=Duration.hours(1)),
            result_path='$.TrainingJob')

        # Step 2: Create SageMaker Model from training output
        create_model_step = tasks.SageMakerCreateModel(
            self, 'CreateModel',
            model_name=sfn.JsonPath.string_at('$$.Execution.Name'),
            primary_container=tasks.ContainerDefinition(
                image=tasks.DockerImage.from_registry(XGBOOST_IMAGE),
                mode=tasks.Mode.SINGLE_MODEL,
                model_s3_location=tasks.S3Location.from_json_expression(
                    '$.TrainingJob.ModelArtifacts.S3ModelArtifacts')
            ),
            role=sagemaker_role,
            result_path='$.Model')

        # Step 3: Create Endpoint Configuration
        create_endpoint_config_step = tasks.SageMakerCreateEndpointConfig(
            self, 'CreateEndpointConfig',
            endpoint_config_name=sfn.JsonPath.string_at('$$.Execution.Name'),
            production_variants=[tasks.ProductionVariant(
                model_name=sfn.JsonPath.string_at('$$.Execution.Name'),
                variant_name='AllTraffic',
                instance_type=ec2.InstanceType.of(ec2.InstanceClass.M4, ec2.InstanceSize.XLARGE),
                initial_instance_count=1
            )],
            result_path='$.EndpointConfig')

        # Step 4: Create Endpoint
        create_endpoint_step = tasks.SageMakerCreateEndpoint(
            self, 'CreateEndpoint',
            endpoint_name=sfn.JsonPath.string_at('$$.Execution.Name'),
            endpoint_config_name=sfn.JsonPath.string_at('$$.Execution.Name'),
            result_path='$.Endpoint')

        # Wait 60 seconds
        wait_step = sfn.Wait(self, "Wait60Seconds",
            time=sfn.WaitTime.duration(Duration.seconds(60)))

        # Check Endpoint Status
        check_endpoint_status = tasks.CallAwsService(self, "CheckEndpointStatus",
            service="sagemaker",
            action="describeEndpoint",
            parameters={
                "EndpointName.$": "$$.Execution.Name"
            },
            iam_resources=["*"],
            result_path="$.EndpointStatus")

        # Choice state
        is_endpoint_ready = sfn.Choice(self, "IsEndpointReady?")

        # Step 5: Invoke test Lambda
        test_step = tasks.LambdaInvoke(
            self, 'TestEndpoint',
            lambda_function=test_lambda,
            payload_response_only=True,
            payload=sfn.TaskInput.from_object({
                "Endpoint": {
                    "EndpointName": sfn.JsonPath.string_at('$$.Execution.Name')
                }
            }),
            result_path='$.TestResult')

        # Step 6: Invoke cleanup Lambda
        delete_endpoint_step = tasks.LambdaInvoke(
            self, 'DeleteEndpoint',
            lambda_function=delete_lambda,
            payload_response_only=True,
            payload=sfn.TaskInput.from_object({
                "Endpoint": {
                    "EndpointName": sfn.JsonPath.string_at('$$.Execution.Name')
                },
                "EndpointConfig": {
                    "EndpointConfigName": sfn.JsonPath.string_at('$$.Execution.Name')
                },
                "Model": {
                    "ModelName": sfn.JsonPath.string_at('$$.Execution.Name')
                }
            }),
            result_path='$.Cleanup')

        # Chain all steps into a State Machine
        definition = training_step \
            .next(create_model_step) \
            .next(create_endpoint_config_step) \
            .next(create_endpoint_step) \
            .next(wait_step)

        wait_step.next(check_endpoint_status)
        check_endpoint_status.next(is_endpoint_ready)
        
        is_endpoint_ready.when(
            sfn.Condition.string_equals("$.EndpointStatus.EndpointStatus", "InService"), 
            test_step
        )
        is_endpoint_ready.when(
            sfn.Condition.string_equals("$.EndpointStatus.EndpointStatus", "Failed"), 
            delete_endpoint_step
        )
        is_endpoint_ready.otherwise(wait_step)

        test_step.next(delete_endpoint_step)

        state_machine = sfn.StateMachine(self, 'MLOpsStateMachine',
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            timeout=Duration.minutes(30))

        # Trigger Lambda — fires when file uploaded to S3
        trigger_lambda = lambda_.Function(self, 'TriggerLambda',
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler='index.handler',
            code=lambda_.Code.from_asset(os.path.join(os.getcwd(), 'lambda')),
            environment={
                'BUCKET_NAME': bucket.bucket_name,
                'STATE_MACHINE_ARN': state_machine.state_machine_arn
            })
        bucket.grant_read(trigger_lambda)
        state_machine.grant_start_execution(trigger_lambda)

        # S3 event → trigger Lambda
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(trigger_lambda),
            s3.NotificationKeyFilter(prefix='train/'))

        CfnOutput(self, 'BucketName', value=bucket.bucket_name)
        CfnOutput(self, 'StateMachineArn', value=state_machine.state_machine_arn)
