import os
import re
import boto3
import logging
from urllib.parse import urlparse
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
import time


logger = logging.getLogger(__name__)


class AssetManager:
    def __init__(self):
        """Initialize AssetManager with S3 client and retry configuration"""
        region = os.getenv("APP_AWS_REGION", "us-east-2")
        self.s3_client = boto3.client(
            "s3",
            region_name=region,
            config=Config(
                retries={"max_attempts": 3, "mode": "adaptive"},
                max_pool_connections=50,
                signature_version="s3v4",
                s3={"addressing_style": "virtual"},
            ),
        )
        self.s3_uri_pattern = re.compile(r"^s3://([^/]+)/(.+)$")
        self.retry_attempts = 3
        self.timeout = 30
        self.backoff_base = 2

        # HTTP error categorization
        self.permanent_http_errors = {400, 401, 403, 404, 405, 410, 422}
        self.temporary_http_errors = {
            408,
            429,
            500,
            502,
            503,
            504,
            520,
            521,
            522,
            523,
            524,
        }

    def download_asset(self, source_uri, temp_dir):
        """Download asset from S3, HTTP/HTTPS, or copy local file"""
        if self._is_s3_uri(source_uri):
            return self._download_from_s3(source_uri, temp_dir)
        elif self._is_http_uri(source_uri):
            return self._download_from_url(source_uri, temp_dir)
        else:
            return self._copy_local_file(source_uri, temp_dir)

    def upload_result(self, local_path, destination_uri, filename):
        """Upload result to S3 or save to local destination"""
        if self._is_s3_uri(destination_uri):
            return self._upload_to_s3(local_path, destination_uri, filename)
        else:
            return self._save_to_local(local_path, destination_uri, filename)

    def _upload_to_s3(self, local_path, destination_uri, filename):
        """Upload result to S3 destination"""
        bucket, key_prefix = self._parse_s3_uri(destination_uri)
        key = f"{key_prefix.rstrip('/')}/{filename}"

        try:
            logger.info(f"Uploading {local_path} to s3://{bucket}/{key}")
            self.s3_client.upload_file(local_path, bucket, key)
            result_url = f"s3://{bucket}/{key}"
            logger.info(f"Successfully uploaded to {result_url}")
            return result_url, bucket, key
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise

    def _save_to_local(self, local_path, destination_path, filename):
        """Save result to local destination"""
        import shutil

        # Ensure destination directory exists
        os.makedirs(destination_path, exist_ok=True)

        # Create final destination path
        final_path = os.path.join(destination_path, filename)

        try:
            logger.info(f"Copying {local_path} to {final_path}")
            shutil.copy2(local_path, final_path)
            logger.info(f"Successfully saved to {final_path}")
            return final_path, None, None
        except Exception as e:
            logger.error(f"Failed to save to local destination: {e}")
            raise

    def _is_s3_uri(self, uri):
        """Check if URI is S3 format"""
        return self.s3_uri_pattern.match(uri) is not None

    def _is_http_uri(self, uri):
        """Check if URI is HTTP/HTTPS format"""
        return uri.startswith(("http://", "https://"))

    def _parse_s3_uri(self, s3_uri):
        """Parse S3 URI into bucket and key"""
        match = self.s3_uri_pattern.match(s3_uri)
        if not match:
            raise ValueError(f"Invalid S3 URI format: {s3_uri}")
        return match.group(1), match.group(2)

    def _download_from_s3(self, s3_uri, temp_dir):
        """Download file from S3 with retry logic"""
        bucket, key = self._parse_s3_uri(s3_uri)
        filename = os.path.basename(key)
        local_path = os.path.join(temp_dir, filename)

        for attempt in range(self.retry_attempts):
            try:
                logger.info(
                    f"Downloading s3://{bucket}/{key} to {local_path} (attempt {attempt + 1})"
                )
                self.s3_client.download_file(bucket, key, local_path)
                logger.info(f"Successfully downloaded {s3_uri}")
                return local_path
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                logger.error(
                    f"S3 download failed - Bucket: '{bucket}', Key: '{key}', Error: {error_code}"
                )
                if error_code in ["NoSuchBucket", "NoSuchKey", "404"]:
                    raise FileNotFoundError(f"S3 object not found: s3://{bucket}/{key}")
                elif error_code in ["AccessDenied", "403"]:
                    raise PermissionError(
                        f"Access denied to S3 object: s3://{bucket}/{key}"
                    )
                else:
                    logger.warning(f"S3 download attempt {attempt + 1} failed: {e}")
                    if attempt == self.retry_attempts - 1:  # Last attempt
                        raise
                    time.sleep(self.backoff_base**attempt)  # Exponential backoff

    def _download_from_url(self, url, temp_dir):
        """Download file from HTTP/HTTPS URL with retry logic"""
        import requests

        filename = (
            os.path.basename(urlparse(url).path)
            or f"url_download_{id(url) % 10000}.tmp"
        )
        local_path = os.path.join(temp_dir, filename)

        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Downloading {url} (attempt {attempt + 1})")
                response = requests.get(url, stream=True, timeout=self.timeout)

                if response.status_code in self.permanent_http_errors:
                    raise requests.exceptions.HTTPError(
                        f"HTTP {response.status_code} error downloading {url}"
                    )

                response.raise_for_status()

                with open(local_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=65536):
                        f.write(chunk)

                logger.info(f"Successfully downloaded {url}")
                return local_path
            except requests.exceptions.HTTPError as e:
                if any(str(code) in str(e) for code in self.permanent_http_errors):
                    raise
                logger.warning(
                    f"URL download attempt {attempt + 1} failed with HTTP error: {e}"
                )
            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.SSLError,
            ) as e:
                logger.warning(f"URL download attempt {attempt + 1} network error: {e}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"URL download attempt {attempt + 1} failed: {e}")

            if attempt == self.retry_attempts - 1:
                raise
            time.sleep(self.backoff_base**attempt)

    def _copy_local_file(self, source_path, temp_dir):
        """Copy local file to temp directory"""
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Local file not found: {source_path}")

        filename = os.path.basename(source_path)
        local_path = os.path.join(temp_dir, filename)

        try:
            import shutil

            shutil.copy2(source_path, local_path)
            logger.info(f"Copied local file {source_path} to {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"Failed to copy local file: {e}")
            raise

    def generate_presigned_url(self, bucket, key, expiration_seconds=None):
        """Generate pre-signed URL for S3 object"""
        if expiration_seconds is None:
            expiration_seconds = int(
                os.getenv("S3_PRESIGNED_URL_EXPIRATION", "86400")
            )  # 24 hours default

        try:
            presigned_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expiration_seconds,
            )
            return presigned_url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
