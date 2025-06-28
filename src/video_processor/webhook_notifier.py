import json
import logging
import time
import os
from typing import Optional, Dict, Any
import requests
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class WebhookNotifier:
    def __init__(self):
        self.retry_attempts = 3
        self.timeout = 30
        self.backoff_base = 2

        # Error categorization
        self.permanent_errors = {400, 401, 403, 404, 405, 410, 422}
        self.temporary_errors = {408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524}

    def send_notification(self, webhook_config, payload: Dict[str, Any]) -> bool:
        """Send webhook notification with retry logic"""
        if not webhook_config:
            return True

        url = str(webhook_config.url)
        method = webhook_config.method
        headers = webhook_config.headers or {}

        # Add default headers
        headers.setdefault("Content-Type", "application/json")
        headers.setdefault("User-Agent", "Auto-Vid/1.0")

        # Add user metadata to payload
        if webhook_config.metadata:
            payload["metadata"] = webhook_config.metadata

        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Sending webhook to {url} (attempt {attempt + 1})")
                response = requests.request(
                    method=method,
                    url=url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )

                if response.status_code < 400:
                    logger.info(f"Webhook notification sent successfully to {url}")
                    return True
                elif response.status_code in self.permanent_errors:
                    logger.error(
                        f"Webhook failed with permanent error {response.status_code}: {response.text}"
                    )
                    return False
                elif (
                    response.status_code in self.temporary_errors
                    or response.status_code >= 500
                ):
                    logger.warning(
                        f"Webhook attempt {attempt + 1} failed with temporary error {response.status_code}"
                    )
                else:
                    logger.warning(
                        f"Webhook attempt {attempt + 1} failed with status {response.status_code}"
                    )

            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.SSLError,
            ) as e:
                logger.warning(f"Webhook attempt {attempt + 1} network error: {str(e)}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Webhook attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.retry_attempts - 1:  # Last attempt
                    break

            # Exponential backoff: 1s, 2s, 4s
            if attempt < self.retry_attempts - 1:
                time.sleep(self.backoff_base**attempt)

        logger.error(
            f"Webhook notification failed after {self.retry_attempts} attempts: {url}"
        )
        return False

    def create_payload(
        self,
        job_id: str,
        status: str,
        processing_time: float,
        output_url: Optional[str] = None,
        s3_uri: Optional[str] = None,
        error: Optional[str] = None,
        duration: Optional[float] = None,
        file_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create webhook payload"""
        payload = {
            "jobId": job_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processingTime": round(processing_time, 2),
        }

        from datetime import timedelta
        
        # Always include all output fields
        output_payload = {
            "url": output_url,
            "urlExpiresAt": None,
            "s3Uri": s3_uri,
            "duration": duration,
            "size": file_size
        }
        
        # Only set expiration if we have a presigned URL
        if output_url and s3_uri and output_url.startswith('https://'):
            expiration_seconds = int(os.getenv('S3_PRESIGNED_URL_EXPIRATION', '86400'))
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expiration_seconds)
            output_payload["urlExpiresAt"] = expires_at.isoformat()
            
        payload["output"] = output_payload

        if error:
            payload["error"] = error

        return payload
