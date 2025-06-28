from typing import Dict, Any, Optional
from datetime import datetime, timezone


def create_standardized_response(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized response format for all API endpoints"""
    return {
        'jobId': job_data['jobId'],
        'status': job_data['status'],
        'submittedAt': job_data.get('submittedAt'),
        'updatedAt': job_data.get('updatedAt'),
        'completedAt': job_data.get('completedAt'),
        'processingTime': job_data.get('processingTime'),
        'output': {
            'url': job_data.get('resultUrl'),
            'urlExpiresAt': job_data.get('urlExpiresAt'),
            's3Uri': job_data.get('s3Uri'),
            'duration': job_data.get('duration'),
            'size': job_data.get('size')
        },
        'error': job_data.get('error'),
        'metadata': job_data.get('metadata', {})
    }