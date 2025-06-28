import json
import logging
import time
import os
from typing import Optional, Dict, Any
import requests
from datetime import datetime, timezone, timedelta
from response_formatter import create_standardized_response

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
        job_info: Optional[Dict[str, Any]] = None,
        output_url: Optional[str] = None,
        s3_uri: Optional[str] = None,
        error: Optional[str] = None,
        duration: Optional[float] = None,
        file_size: Optional[int] = None,
        submitted_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create webhook payload using shared response formatter"""
        completed_at = datetime.now(timezone.utc).isoformat() if status in ["completed", "failed"] else None
        url_expires_at = None
        
        if output_url and s3_uri and output_url.startswith("https://"):
            expiration_seconds = int(os.getenv("S3_PRESIGNED_URL_EXPIRATION", "86400"))
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expiration_seconds)
            url_expires_at = expires_at.isoformat()

        return create_standardized_response(
            job_id=job_id,
            status=status,
            submitted_at=submitted_at,
            updated_at=updated_at,
            completed_at=completed_at,
            processing_time=round(processing_time, 2),
            output_url=output_url,
            url_expires_at=url_expires_at,
            s3_uri=s3_uri,
            duration=duration,
            file_size=file_size,
            error=error,
            job_info=job_info,
            metadata=None  # Webhook metadata handled by send_notification
        )
