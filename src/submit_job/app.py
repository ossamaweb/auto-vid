import json
import uuid
import boto3
import sys
import os
from datetime import datetime, timezone

from job_validator import validate_job_spec


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        job_spec_dict = body["jobSpec"]

        # Validate job spec
        try:
            job_spec = validate_job_spec(job_spec_dict)
        except ValueError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": str(e)}),
            }

        job_id = str(uuid.uuid4())

        # Send job to SQS queue
        sqs = boto3.client("sqs")
        queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/auto-vid-jobs"

        message = {
            "jobId": job_id,
            "jobSpec": job_spec_dict,
            "submittedAt": datetime.now(timezone.utc).isoformat(),
        }

        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message))

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "jobId": job_id,
                    "status": "submitted",
                    "message": "Job submitted successfully",
                }
            ),
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
