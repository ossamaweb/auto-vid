import json
import uuid
import boto3
import os
from datetime import datetime, timezone
from typing import Dict, Any

from job_validator import validate_job_spec
from job_status_manager import JobStatusManager


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
        job_info = extract_job_info(job_spec_dict)

        # Initialize job status manager
        job_manager = JobStatusManager()

        # Create job record in DynamoDB and get standardized response
        response_data = job_manager.create_job(job_id, job_spec_dict, job_info)

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


def extract_job_info(job_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Extract job info from job spec for tracking"""
    job_info = {}

    if "jobInfo" in job_spec:
        spec_job_info = job_spec["jobInfo"]
        if "projectId" in spec_job_info:
            job_info["projectId"] = spec_job_info["projectId"]
        if "title" in spec_job_info:
            job_info["title"] = spec_job_info["title"]
        if "tags" in spec_job_info:
            job_info["tags"] = spec_job_info["tags"]

    if "output" in job_spec and "filename" in job_spec["output"]:
        job_info["outputFilename"] = job_spec["output"]["filename"]

    return job_info
