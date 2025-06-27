import json
import logging
import time
from typing import Optional, Dict, Any
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class WebhookNotifier:
    def __init__(self):
        self.retry_attempts = 3
        self.timeout = 30

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
                elif response.status_code < 500:
                    # 4xx errors - don't retry
                    logger.error(
                        f"Webhook failed with client error {response.status_code}: {response.text}"
                    )
                    return False
                else:
                    # 5xx errors - retry
                    logger.warning(
                        f"Webhook attempt {attempt + 1} failed with server error {response.status_code}"
                    )

            except requests.exceptions.Timeout:
                logger.warning(f"Webhook attempt {attempt + 1} timed out")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Webhook attempt {attempt + 1} connection failed")
            except Exception as e:
                logger.error(f"Webhook attempt {attempt + 1} failed: {str(e)}")

            # Exponential backoff: 1s, 2s, 4s
            if attempt < self.retry_attempts - 1:
                time.sleep(2**attempt)

        logger.error(
            f"Webhook notification failed after {self.retry_attempts} attempts"
        )
        return False

    def create_payload(
        self,
        job_id: str,
        status: str,
        processing_time: float,
        output_url: Optional[str] = None,
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

        payload["output"] = {"url": output_url, "duration": duration, "size": file_size}

        if error:
            payload["error"] = error

        return payload
