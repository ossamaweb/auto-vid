import os
import boto3
import requests
from urllib.parse import urlparse
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class AssetManager:
    def __init__(self):
        self.s3_client = boto3.client('s3')
    
    def download_asset(self, source_url, temp_dir):
        try:
            # Handle local file paths
            if not source_url.startswith(('http://', 'https://', 's3://')):
                return self._copy_local_file(source_url, temp_dir)
            
            parsed_url = urlparse(source_url)
            filename = os.path.basename(parsed_url.path) or 'downloaded_file'
            local_path = os.path.join(temp_dir, filename)
            
            if source_url.startswith('s3://'):
                bucket = parsed_url.netloc
                key = parsed_url.path.lstrip('/')
                self.s3_client.download_file(bucket, key, local_path)
                logger.info(f"Downloaded from S3: s3://{bucket}/{key}")
            else:
                response = requests.get(source_url, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"Downloaded from URL: {source_url}")
            
            return local_path
            
        except ClientError as e:
            logger.error(f"S3 download failed: {str(e)}")
            raise Exception(f"Failed to download from S3: {str(e)}")
        except requests.RequestException as e:
            logger.error(f"HTTP download failed: {str(e)}")
            raise Exception(f"Failed to download from URL: {str(e)}")
        except Exception as e:
            logger.error(f"Asset download failed: {str(e)}")
            raise
    
    def _copy_local_file(self, source_path, temp_dir):
        """Copy local file to temp directory"""
        try:
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"Local file not found: {source_path}")
            
            filename = os.path.basename(source_path)
            local_path = os.path.join(temp_dir, filename)
            
            # Copy file to temp directory
            import shutil
            shutil.copy2(source_path, local_path)
            
            logger.info(f"Copied local file: {source_path} -> {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Local file copy failed: {str(e)}")
            raise Exception(f"Failed to copy local file: {str(e)}")
    
    def upload_result(self, local_path, destination, filename):
        try:
            # Handle local destination paths
            if not destination.startswith('s3://'):
                return self._copy_to_local_destination(local_path, destination, filename)
            
            parsed_dest = urlparse(destination)
            bucket = parsed_dest.netloc
            key = os.path.join(parsed_dest.path.lstrip('/'), filename)
            
            self.s3_client.upload_file(local_path, bucket, key)
            result_url = f"s3://{bucket}/{key}"
            logger.info(f"Uploaded result to: {result_url}")
            return result_url
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise Exception(f"Failed to upload to S3: {str(e)}")
        except Exception as e:
            logger.error(f"Result upload failed: {str(e)}")
            raise
    
    def _copy_to_local_destination(self, local_path, destination, filename):
        """Copy result to local destination"""
        try:
            import shutil
            os.makedirs(destination, exist_ok=True)
            dest_path = os.path.join(destination, filename)
            shutil.copy2(local_path, dest_path)
            
            logger.info(f"Copied result to local destination: {dest_path}")
            return dest_path
            
        except Exception as e:
            logger.error(f"Local destination copy failed: {str(e)}")
            raise Exception(f"Failed to copy to local destination: {str(e)}")