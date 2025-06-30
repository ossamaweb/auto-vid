# Architecture Details

## Core Components

- **Submit Job API** - Validates job specs and queues processing via SQS
- **Video Processor** - Handles video generation with MoviePy and AWS Polly
- **Status API** - Returns job progress and completion status
- **Managed S3 Bucket** - Automatic storage for assets and outputs
- **Shared Layer** - Pydantic models and validation logic

## AWS Services Used

- **Lambda** - Serverless compute with 15-minute timeout support
- **API Gateway** - RESTful API endpoints with API key authentication and rate limiting
- **SQS** - Reliable job queuing with dead letter handling
- **S3** - Asset storage with lifecycle management
- **Polly** - Neural and generative text-to-speech
- **CloudFormation** - Infrastructure as Code via SAM
- **DynamoDB** - Job status tracking with TTL
- **ECR** - Container image storage

## Configuration

### Environment Variables

- `S3_BUCKET_NAME` - Managed S3 bucket name (auto-configured)
- `APP_AWS_REGION` - AWS region for S3 operations (auto-configured)
- `WEBHOOK_MAX_HEADERS_SIZE` - Maximum webhook headers size (default: 1024)
- `WEBHOOK_MAX_METADATA_SIZE` - Maximum webhook metadata size (default: 1024)
- `S3_PRESIGNED_URL_EXPIRATION` - Pre-signed URL expiration (default: 86400)
- `DYNAMODB_JOBS_TTL_SECONDS` - Job record TTL (default: 604800 = 7 days)
- `LOG_LEVEL` - Logging verbosity level (default: INFO, options: DEBUG, INFO, WARNING, ERROR)

### Resource Naming

All AWS resources use consistent naming with service type identification:

- S3 Bucket: `auto-vid-s3-bucket-{stack-name}-{account-id}`
- SQS Queue: `auto-vid-sqs-jobs-{stack-name}-{account-id}`
- DynamoDB Table: `auto-vid-dynamodb-jobs-{stack-name}-{account-id}`
- Lambda Layer: `auto-vid-layer-shared-{stack-name}-{account-id}`
- API Key: `auto-vid-api-key`
- Usage Plan: `auto-vid-usage-plan`

### API Security

**Authentication:**
- API key required for all endpoints
- Key managed through AWS API Gateway console
- Header: `X-API-Key: your-actual-key-value`

**Rate Limiting:**
- **Throttle:** 2 requests per second with 5 burst capacity
- **Quota:** 50 requests per day
- **Enforcement:** API Gateway usage plans
- **Response:** 429 Too Many Requests when exceeded

### Managed S3 Bucket

- **Automatic Creation** - No manual S3 setup required
- **Organized Structure** - `/assets/` and `/outputs/` prefixes
- **Security** - Private bucket with proper IAM policies
- **Flexibility** - Can override with custom S3 URIs

## Performance & Limits

### Lambda Configuration

**API Functions (Submit/Status):**

- **Memory**: 256-512 MB (lightweight JSON processing)
- **Timeout**: 30-60 seconds (fast API responses)
- **Storage**: Default 512 MB (no file processing needed)

**Video Processor:**

- **Memory**: 3,008 MB (compatible with all AWS accounts)
- **Timeout**: 15 minutes (maximum allowed)
- **Storage**: 10 GB ephemeral storage (large video files)
- **Container Size**: ~360MB (optimized multi-stage build)

### Supported Formats

- **Video Input**: MP4, AVI, MOV, MKV
- **Audio Input**: MP3, WAV, M4A, FLAC
- **Video Output**: MP4 with H.264/AAC

## Production Features

- **✅ Input Validation** - Comprehensive Pydantic models
- **✅ Error Handling** - Retry logic and detailed error messages
- **✅ Security** - API key authentication, IAM least privilege, and input sanitization
- **✅ Rate Limiting** - 2 req/sec, 5 burst, 50/day quota to prevent abuse
- **✅ Monitoring** - CloudWatch logs and metrics
- **✅ Scalability** - SQS queuing and Lambda concurrency
- **✅ Cost Optimization** - Pay-per-use serverless architecture

## Advanced Features

- **Empty Timeline Support** - Create videos with just background music
- **Audio Ducking** - Automatically lower background music during speech
- **Multiple TTS Engines** - Standard, neural, long-form, and generative
- **SSML Support** - Advanced speech markup for pronunciation control
- **Crossfading** - Smooth transitions between background music tracks
- **Pre-signed Download URLs** - Secure, time-limited download links
- **Webhook Notifications** - Real-time completion notifications with custom headers and metadata

## Webhook Payload Structure

When jobs complete, webhooks receive a JSON payload:

```json
{
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "submittedAt": "2024-01-15T10:25:00.000000+00:00",
  "updatedAt": "2024-01-15T10:30:45.123456+00:00",
  "completedAt": "2024-01-15T10:30:45.123456+00:00",
  "processingTime": 127.45,
  "output": {
    "url": "https://bucket.s3.amazonaws.com/outputs/my-video.mp4?X-Amz-Algorithm=...",
    "urlExpiresAt": "2024-01-16T10:30:45.123456+00:00",
    "s3Uri": "s3://auto-vid-bucket/outputs/my-video.mp4",
    "duration": 90.2,
    "size": 15728640
  },
  "error": null,
  "jobInfo": {
    "projectId": "demo_project",
    "title": "Welcome Video"
  },
  "metadata": {
    "project": "demo",
    "priority": "high"
  }
}
```
