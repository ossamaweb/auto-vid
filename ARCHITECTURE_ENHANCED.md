# Enhanced Submit Job Lambda Architecture

## Overview

The Submit Job Lambda function has been enhanced with production-ready features including job tracking, proper error handling, and environment variable management.

## Key Improvements

### 1. **DynamoDB Job Tracking**

- **Table**: `auto-vid-dynamodb-jobs-{stack-name}-{account-id}`
- **TTL**: 7 days automatic cleanup
- **Status Tracking**: submitted → processing → completed/failed/retrying
- **Full Job Spec Storage**: Complete job specifications stored for debugging and reprocessing

### 2. **Environment Variables**

- `SQS_JOB_QUEUE_URL`: SQS queue URL from CloudFormation
- `DYNAMODB_JOBS_TABLE`: DynamoDB table name
- `S3_BUCKET_NAME`: Managed S3 bucket

### 3. **Enhanced Error Handling**

- Input validation with detailed error messages
- Standardized error responses with timestamps
- Proper HTTP status codes and headers

### 4. **Job Status Manager**

- Centralized DynamoDB operations
- Consistent status updates across all functions
- Metadata extraction and storage

## Architecture Flow

```
API Gateway → Submit Job Lambda → DynamoDB (create job) → SQS → Video Processor
                                                                      ↓
Get Status Lambda ← DynamoDB (read job) ← DynamoDB (update status) ←
```

## Job Status States

1. **submitted** - Job received and queued
2. **processing** - Video processing started
3. **completed** - Job finished successfully
4. **failed** - Permanent failure (no retry)
5. **retrying** - Transient failure (will retry)

## API Responses

### Submit Job Success

```json
{
  "jobId": "uuid",
  "status": "submitted",
  "submittedAt": "2024-01-01T12:00:00Z",
  "updatedAt": "2024-01-01T12:00:00Z",
  "completedAt": null,
  "processingTime": null,
  "output": {
    "url": null,
    "urlExpiresAt": null,
    "s3Uri": null,
    "duration": null,
    "size": null
  },
  "error": null,
  "metadata": {}
}
```

### Get Status Response

```json
{
  "jobId": "uuid",
  "status": "processing",
  "submittedAt": "2024-01-01T12:00:00Z",
  "updatedAt": "2024-01-01T12:01:00Z",
  "completedAt": null,
  "processingTime": null,
  "output": {
    "url": null,
    "urlExpiresAt": null,
    "s3Uri": null,
    "duration": null,
    "size": null
  },
  "error": null,
  "metadata": {
    "projectId": "example",
    "outputFilename": "video.mp4"
  }
}
```

## Deployment

The enhanced architecture requires no additional manual setup - all resources are created automatically via CloudFormation:

```bash
sam build
sam deploy
```

## Benefits

- **Production Ready**: Proper error handling and status tracking
- **Scalable**: DynamoDB auto-scaling and SQS queuing
- **Observable**: CloudWatch logs and DynamoDB metrics
- **Cost Effective**: Pay-per-use with TTL cleanup
- **Reliable**: Retry logic and transient error handling
