import boto3
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from response_formatter import create_standardized_response


class JobStatusManager:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb")
        self.table_name = os.environ["JOB_STATUS_TABLE"]
        self.table = self.dynamodb.Table(self.table_name)

    def create_job(
        self,
        job_id: str,
        job_spec: Dict[Any, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new job record with submitted status and return standardized response"""
        timestamp = datetime.now(timezone.utc).isoformat()
        ttl_seconds = int(
            os.environ.get("DYNAMODB_JOB_TTL_SECONDS", str(7 * 24 * 60 * 60))
        )
        ttl = int(datetime.now(timezone.utc).timestamp()) + ttl_seconds

        item = {
            "jobId": job_id,
            "status": "submitted",
            "submittedAt": timestamp,
            "updatedAt": timestamp,
            "jobSpec": job_spec,
            "ttl": ttl,
        }

        if metadata:
            item["metadata"] = metadata

        self.table.put_item(Item=item)

        return create_standardized_response(item)

    def update_status(self, job_id: str, status: str, **kwargs) -> None:
        """Update job status with optional additional fields"""
        update_expr = "SET #status = :status, updatedAt = :updated"
        expr_values = {
            ":status": status,
            ":updated": datetime.now(timezone.utc).isoformat(),
        }
        expr_names = {"#status": "status"}

        for key, value in kwargs.items():
            if value is not None:
                update_expr += f", {key} = :{key}"
                expr_values[f":{key}"] = value

        self.table.update_item(
            Key={"jobId": job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames=expr_names,
        )

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and details"""
        try:
            response = self.table.get_item(Key={"jobId": job_id})
            return response.get("Item")
        except Exception:
            return None
