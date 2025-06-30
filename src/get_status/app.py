import json
from datetime import datetime, timezone
from typing import Dict, Any
from job_manager import JobManager


def lambda_handler(event, context):
    """Get job status from DynamoDB"""
    try:
        # Validate path parameters
        if not event.get("pathParameters") or not event["pathParameters"].get("jobId"):
            return create_error_response(400, "Missing jobId in path parameters")

        job_id = event["pathParameters"]["jobId"]

        # Get job status from DynamoDB
        job_manager = JobManager()
        job_data = job_manager.get_job(job_id)

        if not job_data:
            return create_error_response(404, f"Job {job_id} not found")

        # Remove DynamoDB-specific fields and return standardized response
        standardized_response = {k: v for k, v in job_data.items() if k not in ["ttl"]}

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(standardized_response, default=str),
        }

    except Exception as e:
        print(f"Error getting job status: {str(e)}")
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
