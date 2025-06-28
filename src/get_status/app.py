import json
from datetime import datetime, timezone
from typing import Dict, Any
from job_status_manager import JobStatusManager
from response_formatter import create_standardized_response


def lambda_handler(event, context):
    """Get job status from DynamoDB"""
    try:
        # Validate path parameters
        if not event.get("pathParameters") or not event["pathParameters"].get("jobId"):
            return create_error_response(400, "Missing jobId in path parameters")

        job_id = event["pathParameters"]["jobId"]

        # Get job status from DynamoDB
        job_manager = JobStatusManager()
        job_data = job_manager.get_job(job_id)

        if not job_data:
            return create_error_response(404, f"Job {job_id} not found")

        standardized_response = create_standardized_response(job_data)

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
