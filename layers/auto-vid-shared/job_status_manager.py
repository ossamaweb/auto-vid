import boto3
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class JobStatusManager:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ['JOB_STATUS_TABLE']
        self.table = self.dynamodb.Table(self.table_name)
    
    def create_job(self, job_id: str, job_spec: Dict[Any, Any], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Create a new job record with submitted status"""
        timestamp = datetime.now(timezone.utc).isoformat()
        ttl = int(datetime.now(timezone.utc).timestamp()) + (7 * 24 * 60 * 60)  # 7 days TTL
        
        item = {
            'jobId': job_id,
            'status': 'submitted',
            'submittedAt': timestamp,
            'updatedAt': timestamp,
            'ttl': ttl
        }
        
        if metadata:
            item['metadata'] = metadata
            
        self.table.put_item(Item=item)
    
    def update_status(self, job_id: str, status: str, **kwargs) -> None:
        """Update job status with optional additional fields"""
        update_expr = "SET #status = :status, updatedAt = :updated"
        expr_values = {
            ':status': status,
            ':updated': datetime.now(timezone.utc).isoformat()
        }
        expr_names = {'#status': 'status'}
        
        for key, value in kwargs.items():
            if value is not None:
                update_expr += f", {key} = :{key}"
                expr_values[f':{key}'] = value
        
        self.table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames=expr_names
        )
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and details"""
        try:
            response = self.table.get_item(Key={'jobId': job_id})
            return response.get('Item')
        except Exception:
            return None