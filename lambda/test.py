import boto3, json

sagemaker_runtime = boto3.client('sagemaker-runtime')

def handler(event, context):
    endpoint_name = event['Endpoint']['EndpointName']
    test_data = '0.5'
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='text/csv',
        Body=test_data
    )
    return {'endpoint': endpoint_name, 'test_input': test_data,
            'prediction': response['Body'].read().decode()}
