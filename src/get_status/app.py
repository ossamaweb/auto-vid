import json
import boto3

def lambda_handler(event, context):
    try:
        job_id = event['pathParameters']['jobId']
        
        # In a real implementation, you would query a database
        # For now, return a mock status
        status_data = {
            'jobId': job_id,
            'status': 'processing',
            'progress': 75,
            'message': 'Video processing in progress'
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(status_data)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }