import json
import logging
import sys
import os
from botocore.exceptions import ClientError
from .video_processor import VideoProcessor

# Add shared directory to path
shared_path = os.path.join(os.path.dirname(__file__), "..", "shared")
sys.path.insert(0, os.path.abspath(shared_path))
from job_validator import validate_job_spec  # noqa: E402

logger = logging.getLogger(__name__)


def is_transient_error(error):
    """Determine if error is transient and should be retried"""
    error_str = str(error).lower()

    # AWS service errors that should be retried
    if isinstance(error, ClientError):
        error_code = error.response.get("Error", {}).get("Code", "")
        if error_code in ["ServiceUnavailable", "Throttling", "RequestTimeout"]:
            return True

    # Network and temporary issues
    transient_indicators = [
        "timeout",
        "connection",
        "network",
        "temporary",
        "service unavailable",
        "throttl",
        "rate limit",
    ]

    return any(indicator in error_str for indicator in transient_indicators)


def lambda_handler(event, context):
    failed_jobs = []

    # Parse SQS message
    for record in event["Records"]:
        message_body = json.loads(record["body"])
        job_id = message_body["jobId"]
        job_spec_dict = message_body["jobSpec"]

        try:
            # Validate job spec (permanent failure)
            job_spec = validate_job_spec(job_spec_dict)

            # Process video job
            processor = VideoProcessor()
            result_url = processor.process_video_job(job_id, job_spec)

            logger.info(f"Job {job_id} completed successfully. Result: {result_url}")

        except ValueError as e:
            # Permanent error (validation failure) - don't retry
            logger.error(f"Job {job_id} permanently failed (validation): {str(e)}")

        except Exception as e:
            # Check if error is transient
            if is_transient_error(e):
                logger.warning(f"Job {job_id} failed with transient error: {str(e)}")
                failed_jobs.append(job_id)
            else:
                # Permanent error - don't retry
                logger.error(f"Job {job_id} permanently failed: {str(e)}")

    # If any jobs had transient failures, raise exception to trigger SQS retry
    if failed_jobs:
        raise Exception(f"Transient failures for jobs: {', '.join(failed_jobs)}")

    return {"statusCode": 200, "body": "Jobs processed successfully"}
