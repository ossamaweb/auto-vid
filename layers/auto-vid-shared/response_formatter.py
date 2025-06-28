from typing import Dict, Any, Optional
from datetime import datetime, timezone


def create_standardized_response(
    job_id: str,
    status: str,
    submitted_at: Optional[str] = None,
    updated_at: Optional[str] = None,
    completed_at: Optional[str] = None,
    processing_time: Optional[float] = None,
    output_url: Optional[str] = None,
    url_expires_at: Optional[str] = None,
    s3_uri: Optional[str] = None,
    duration: Optional[float] = None,
    file_size: Optional[int] = None,
    error: Optional[str] = None,
    job_info: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized response format for all API endpoints"""
    return {
        'jobId': job_id,
        'status': status,
        'submittedAt': submitted_at,
        'updatedAt': updated_at,
        'completedAt': completed_at,
        'processingTime': processing_time,
        'output': {
            'url': output_url,
            'urlExpiresAt': url_expires_at,
            's3Uri': s3_uri,
            'duration': duration,
            'size': file_size
        },
        'error': error,
        'jobInfo': job_info or {},
        'metadata': metadata or {}
    }