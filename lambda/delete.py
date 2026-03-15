import boto3

sagemaker = boto3.client('sagemaker')

def handler(event, context):
    sagemaker.delete_endpoint(EndpointName=event['Endpoint']['EndpointName'])
    sagemaker.delete_endpoint_config(EndpointConfigName=event['EndpointConfig']['EndpointConfigName'])
    sagemaker.delete_model(ModelName=event['Model']['ModelName'])
    return {'status': 'cleanup initiated'}
