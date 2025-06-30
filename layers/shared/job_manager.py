import boto3
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from decimal import Decimal
from response_formatter import create_standardized_response


class JobManager:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb")
        self.table_name = os.environ["DYNAMODB_JOBS_TABLE"]
        self.table = self.dynamodb.Table(self.table_name)

    def _convert_for_dynamodb(self, data):
        """Convert floats to Decimal for DynamoDB compatibility"""
        if isinstance(data, dict):
            return {k: self._convert_for_dynamodb(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_for_dynamodb(item) for item in data]
        elif isinstance(data, float):
            return Decimal(str(data))
        else:
            return data

    def _convert_from_dynamodb(self, data):
        """Convert Decimal back to float for API responses"""
        if isinstance(data, dict):
            return {k: self._convert_from_dynamodb(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_from_dynamodb(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        else:
            return data

    def create_job(
        self,
        job_id: str,
        job_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new job record with submitted status and return standardized response"""
        timestamp = datetime.now(timezone.utc).isoformat()
        ttl_seconds = int(os.environ.get("DYNAMODB_JOBS_TTL_SECONDS", "604800"))
        ttl = int(datetime.now(timezone.utc).timestamp()) + ttl_seconds

        response_item = create_standardized_response(
            job_id=job_id,
            status="submitted",
            submitted_at=timestamp,
            updated_at=timestamp,
            job_info=job_info,
        )

        # Add DynamoDB-specific fields and convert types
        db_item = response_item.copy()
        db_item["ttl"] = ttl
        db_item = self._convert_for_dynamodb(db_item)

        self.table.put_item(Item=db_item)

        return response_item

    def update_job_completion(
        self,
        job_id: str,
        status: str,
        processing_time: float,
        output: Dict[str, Any],
        error: Optional[str] = None,
    ) -> None:
        """Update job with completion data"""
        timestamp = datetime.now(timezone.utc).isoformat()

        self.table.update_item(
            Key={"jobId": job_id},
            UpdateExpression="SET #status = :status, updatedAt = :updated, completedAt = :completed, processingTime = :time, #output = :output, #error = :error",
            ExpressionAttributeValues={
                ":status": status,
                ":updated": timestamp,
                ":completed": timestamp if status in ["completed", "failed"] else None,
                ":time": self._convert_for_dynamodb(round(processing_time, 2)),
                ":output": self._convert_for_dynamodb(output),
                ":error": error,
            },
            ExpressionAttributeNames={
                "#status": "status",
                "#output": "output",
                "#error": "error",
            },
        )

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
                expr_values[f":{key}"] = self._convert_for_dynamodb(value)

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
            item = response.get("Item")
            return self._convert_from_dynamodb(item)
        except Exception:
            return None
