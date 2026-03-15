import boto3, os, json

stepfunctions = boto3.client('stepfunctions')

def handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key    = event['Records'][0]['s3']['object']['key']
    response = stepfunctions.start_execution(
        stateMachineArn=os.environ['STATE_MACHINE_ARN'],
        input=json.dumps({'bucket': bucket, 'key': key})
    )
    return {'statusCode': 200,
            'body': json.dumps({'executionArn': response['executionArn']})}
