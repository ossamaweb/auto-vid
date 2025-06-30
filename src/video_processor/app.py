import json
import logging
import sys
import os
from botocore.exceptions import ClientError
from video_processor import VideoProcessor
from webhook_notifier import WebhookNotifier
from asset_manager import AssetManager


# Add layers path for local development and Docker
layers_path = os.path.join(os.path.dirname(__file__), "..", "..", "layers", "shared")
sys.path.insert(0, os.path.abspath(layers_path))
from job_validator import validate_job_spec  # noqa: E402
from job_manager import JobManager  # noqa: E402


# Configure logging for the entire application
level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(level)


class JobProcessor:
    def __init__(self):
        self.job_manager = JobManager()
        self.video_processor = VideoProcessor()
        self.asset_manager = AssetManager()
        self.webhook_notifier = WebhookNotifier()
        self.empty_output = {
            "url": None,
            "urlExpiresAt": None,
            "s3Uri": None,
            "duration": None,
            "size": None,
        }


def lambda_handler(event, context):
    transient_failures = []
    permanent_failures = []
    successful_jobs = []
    processor = JobProcessor()

    # Parse SQS message
    for record in event["Records"]:
        message_body = json.loads(record["body"])
        job_id = message_body["jobId"]
        job_spec_dict = message_body["jobSpec"]

        result = process_single_job(processor, job_id, job_spec_dict)

        if result["status"] == "success":
            successful_jobs.append(job_id)
        elif result["status"] == "transient_failure":
            transient_failures.append(job_id)
        else:
            permanent_failures.append(job_id)

    # If any jobs had transient failures, raise exception to trigger SQS retry
    if transient_failures:
        raise Exception(f"Transient failures for jobs: {', '.join(transient_failures)}")

    # Return appropriate status based on results
    if permanent_failures:
        return {
            "statusCode": 400,
            "body": f"Permanent failures: {', '.join(permanent_failures)}. Successful: {', '.join(successful_jobs)}",
        }

    return {
        "statusCode": 200,
        "body": f"All jobs processed successfully: {', '.join(successful_jobs)}",
    }


def process_single_job(processor, job_id, job_spec_dict):
    """Process a single job and return result status"""

    video_result = None

    try:
        # Validate job spec
        job_spec = validate_job_spec(job_spec_dict)

        # Update status to processing
        processor.job_manager.update_status(job_id, "processing")

        # Process video job
        video_result = processor.video_processor.process_video_job(job_id, job_spec)

        if video_result["success"]:
            # Upload and get URLs
            upload_result = upload_file(processor.asset_manager, video_result, job_spec)
            if upload_result["success"]:
                # Update job completion
                output_data = {
                    "url": upload_result["outputUrl"],
                    "urlExpiresAt": upload_result["urlExpiresAt"],
                    "s3Uri": upload_result["s3Uri"],
                    "duration": video_result["duration"],
                    "size": video_result["fileSize"],
                }
                processor.job_manager.update_job_completion(
                    job_id, "completed", video_result["processingTime"], output_data
                )

                # Send success webhook
                send_webhook(
                    job_id,
                    "completed",
                    job_spec,
                    processor.webhook_notifier,
                    video_result,
                    upload_result,
                )

                logger.info(
                    f"Job {job_id} completed successfully. Result: {upload_result['outputUrl']}"
                )

                return {"status": "success"}
            else:
                # Upload failed
                processor.job_manager.update_job_completion(
                    job_id,
                    "failed",
                    video_result["processingTime"],
                    processor.empty_output,
                    upload_result["error"],
                )

                # Send failure webhook
                send_webhook(
                    job_id,
                    "failed",
                    job_spec,
                    processor.webhook_notifier,
                    video_result,
                    None,
                    upload_result["error"],
                )

                logger.error(f"Job {job_id} upload failed: {upload_result['error']}")

                return {"status": "permanent_failure"}
        else:
            # Processing failed
            processor.job_manager.update_job_completion(
                job_id,
                "failed",
                video_result["processingTime"],
                processor.empty_output,
                video_result["error"],
            )

            # Send failure webhook
            send_webhook(
                job_id,
                "failed",
                job_spec,
                processor.webhook_notifier,
                video_result,
                None,
                video_result["error"],
            )

            logger.error(f"Job {job_id} processing failed: {video_result['error']}")

            return {"status": "permanent_failure"}

    except ValueError as e:
        # Permanent error (validation failure)
        processor.job_manager.update_job_completion(
            job_id, "failed", 0, processor.empty_output, str(e)
        )
        logger.error(f"Job {job_id} permanently failed (validation): {str(e)}")
        return {"status": "permanent_failure"}

    except Exception as e:
        # Check if error is transient
        if is_transient_error(e):
            processor.job_manager.update_status(job_id, "retrying", error=str(e))
            logger.warning(f"Job {job_id} failed with transient error: {str(e)}")
            return {"status": "transient_failure"}
        else:
            # Permanent error
            processor.job_manager.update_job_completion(
                job_id, "failed", 0, processor.empty_output, str(e)
            )
            logger.error(f"Job {job_id} permanently failed: {str(e)}")
            return {"status": "permanent_failure"}

    finally:
        # Single cleanCleanup in procesup location
        if video_result and video_result.get("tempDir"):
            processor.video_processor.cleanup_job_dir(video_result["tempDir"])


def upload_file(asset_manager_processor, video_result, job_spec):
    """Upload processed video file and return upload video_result"""
    try:
        # Determine destination
        destination = job_spec.output.destination
        if not destination:
            bucket_name = os.environ.get("S3_BUCKET_NAME")
            if bucket_name:
                destination = f"s3://{bucket_name}/outputs/"
            else:
                raise ValueError(
                    "No output destination specified and no default bucket available"
                )

        # Upload file
        result_path, bucket, key = asset_manager_processor.upload_result(
            video_result["localOutputPath"], destination, video_result["outputFilename"]
        )

        # Generate presigned URL
        if bucket and key:
            s3_uri = f"s3://{bucket}/{key}"
            try:
                presigned_url = asset_manager_processor.generate_presigned_url(
                    bucket, key
                )
                # Calculate URL expiration
                from datetime import datetime, timezone, timedelta

                expiration_seconds = int(
                    os.getenv("S3_PRESIGNED_URL_EXPIRATION", "86400")
                )
                expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=expiration_seconds
                )
                url_expires_at = expires_at.isoformat()
            except Exception as e:
                logger.warning(f"Failed to generate presigned URL: {e}")
                presigned_url = None
                url_expires_at = None
        else:
            presigned_url = result_path
            s3_uri = None
            url_expires_at = None

        return {
            "success": True,
            "outputUrl": presigned_url,
            "s3Uri": s3_uri,
            "urlExpiresAt": url_expires_at,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        return {"success": False, "outputUrl": None, "s3Uri": None, "error": str(e)}


def send_webhook(
    job_id,
    status,
    job_spec,
    webhook_notifier,
    video_result,
    upload_result=None,
    error=None,
):
    """Send webhook notification"""
    if not (job_spec.notifications and job_spec.notifications.webhook):
        return

    job_info = getattr(job_spec, "jobInfo", None)
    job_info_dict = job_info.model_dump() if job_info else None

    if status == "completed" and upload_result:
        payload = webhook_notifier.create_payload(
            job_id=job_id,
            status=status,
            processing_time=video_result["processingTime"],
            job_info=job_info_dict,
            output_url=upload_result["outputUrl"],
            url_expires_at=upload_result["urlExpiresAt"],
            s3_uri=upload_result["s3Uri"],
            duration=video_result["duration"],
            file_size=video_result["fileSize"],
        )
    else:
        payload = webhook_notifier.create_payload(
            job_id=job_id,
            status=status,
            processing_time=video_result["processingTime"],
            job_info=job_info_dict,
            error=error,
        )

    webhook_notifier.send_notification(job_spec.notifications.webhook, payload)


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
