import json
import logging
import sys
import os
from botocore.exceptions import ClientError
from video_processor import VideoProcessor

import sys
import os

# Add layers path for local development and Docker
layers_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "layers", "auto-vid-shared"
)
sys.path.insert(0, os.path.abspath(layers_path))
from job_validator import validate_job_spec  # noqa: E402
from job_status_manager import JobStatusManager  # noqa: E402

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
    transient_failures = []
    permanent_failures = []
    successful_jobs = []
    job_manager = JobStatusManager()

    # Parse SQS message
    for record in event["Records"]:
        message_body = json.loads(record["body"])
        job_id = message_body["jobId"]
        job_spec_dict = message_body["jobSpec"]

        try:
            # Update status to processing
            job_manager.update_status(job_id, "processing")
            
            # Validate job spec (permanent failure)
            job_spec = validate_job_spec(job_spec_dict)

            # Process video job
            processor = VideoProcessor()
            result_url = processor.process_video_job(job_id, job_spec)

            # Update status to completed
            from datetime import datetime, timezone
            job_manager.update_status(
                job_id, 
                "completed", 
                resultUrl=result_url,
                completedAt=datetime.now(timezone.utc).isoformat()
            )

            logger.info(f"Job {job_id} completed successfully. Result: {result_url}")
            successful_jobs.append(job_id)

        except ValueError as e:
            # Permanent error (validation failure) - don't retry
            job_manager.update_status(job_id, "failed", error=str(e))
            logger.error(f"Job {job_id} permanently failed (validation): {str(e)}")
            permanent_failures.append(job_id)

        except Exception as e:
            # Check if error is transient
            if is_transient_error(e):
                job_manager.update_status(job_id, "retrying", error=str(e))
                logger.warning(f"Job {job_id} failed with transient error: {str(e)}")
                transient_failures.append(job_id)
            else:
                # Permanent error - don't retry
                job_manager.update_status(job_id, "failed", error=str(e))
                logger.error(f"Job {job_id} permanently failed: {str(e)}")
                permanent_failures.append(job_id)

    # If any jobs had transient failures, raise exception to trigger SQS retry
    if transient_failures:
        raise Exception(f"Transient failures for jobs: {', '.join(transient_failures)}")

    # Return appropriate status based on results
    if permanent_failures:
        return {
            "statusCode": 400,
            "body": f"Permanent failures: {', '.join(permanent_failures)}. Successful: {', '.join(successful_jobs)}"
        }
    
    return {
        "statusCode": 200, 
        "body": f"All jobs processed successfully: {', '.join(successful_jobs)}"
    }
