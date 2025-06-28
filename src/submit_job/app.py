import json
import uuid
import boto3
import os
from datetime import datetime, timezone
from typing import Dict, Any

from job_validator import validate_job_spec
from job_status_manager import JobManager


def lambda_handler(event, context):
    """Submit job to SQS queue and create job record in DynamoDB"""
    try:
        # Validate request structure
        if not event.get("body"):
            return create_error_response(400, "Missing request body")

        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError:
            return create_error_response(400, "Invalid JSON in request body")

        if "jobSpec" not in body:
            return create_error_response(400, "Missing 'jobSpec' field in request body")

        job_spec_dict = body["jobSpec"]

        # Validate job specification
        try:
            job_spec = validate_job_spec(job_spec_dict)
        except ValueError as e:
            return create_error_response(400, str(e))

        # Generate job ID and extract job info
        job_id = str(uuid.uuid4())
        job_info = job_spec_dict.get("jobInfo")

        # Initialize job manager
        job_manager = JobManager()

        # Create job record in DynamoDB and get standardized response
        response_data = job_manager.create_job(job_id, job_info)

        # Send job to SQS queue
        queue_url = os.environ["JOB_QUEUE_URL"]
        message = {
            "jobId": job_id,
            "jobSpec": job_spec_dict,
            "submittedAt": datetime.now(timezone.utc).isoformat(),
        }

        sqs = boto3.client("sqs")
        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message))

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_data),
        }

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return create_error_response(500, "Internal server error")


def create_error_response(status_code: int, error_message: str) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "error": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
    }
