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
        self.s3_client = boto3.client('s3', config=Config(
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            max_pool_connections=50
        ))
        self.s3_uri_pattern = re.compile(r'^s3://([^/]+)/(.+)$')
    
    def download_asset(self, source_uri, temp_dir):
        """Download asset from S3 or copy local file"""
        if self._is_s3_uri(source_uri):
            return self._download_from_s3(source_uri, temp_dir)
        else:
            return self._copy_local_file(source_uri, temp_dir)
    
    def upload_result(self, local_path, destination_uri, filename):
        """Upload result to S3 destination"""
        if not self._is_s3_uri(destination_uri):
            raise ValueError(f"Destination must be S3 URI: {destination_uri}")
        
        bucket, key_prefix = self._parse_s3_uri(destination_uri)
        key = f"{key_prefix.rstrip('/')}/{filename}"
        
        try:
            logger.info(f"Uploading {local_path} to s3://{bucket}/{key}")
            self.s3_client.upload_file(local_path, bucket, key)
            result_url = f"s3://{bucket}/{key}"
            logger.info(f"Successfully uploaded to {result_url}")
            return result_url
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise
    
    def _is_s3_uri(self, uri):
        """Check if URI is S3 format"""
        return self.s3_uri_pattern.match(uri) is not None
    
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
        
        for attempt in range(3):
            try:
                logger.info(f"Downloading s3://{bucket}/{key} to {local_path} (attempt {attempt + 1})")
                self.s3_client.download_file(bucket, key, local_path)
                logger.info(f"Successfully downloaded {s3_uri}")
                return local_path
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code in ['NoSuchBucket', 'NoSuchKey']:
                    logger.error(f"S3 object not found: {s3_uri}")
                    raise FileNotFoundError(f"S3 object not found: {s3_uri}")
                elif error_code == 'AccessDenied':
                    logger.error(f"Access denied to S3 object: {s3_uri}")
                    raise PermissionError(f"Access denied to S3 object: {s3_uri}")
                else:
                    logger.warning(f"S3 download attempt {attempt + 1} failed: {e}")
                    if attempt == 2:  # Last attempt
                        raise
                    time.sleep(2 ** attempt)  # Exponential backoff
    
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