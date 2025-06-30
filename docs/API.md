# API Reference

Auto-Vid provides a REST API for submitting video processing jobs and checking their status.

## Base URL

After deployment, your API will be available at:

```
https://{api-id}.execute-api.{region}.amazonaws.com/Prod
```

## Authentication

API key authentication is required when deployed with Phase 2. After Phase 2 deployment, retrieve your API key from the AWS Console.

**Required Header (Phase 2 only):**
```
X-API-Key: your-actual-api-key-value
```

**Getting Your API Key:**
1. Go to AWS Console → API Gateway
2. Navigate to API Keys → auto-vid-api-key-{stack-name}
3. Click "Show" to reveal the key value

## Endpoints

### Submit Job

Submit a new video processing job.

**Endpoint:** `POST /submit`

**Request Headers:**

- `Content-Type: application/json`
- `X-API-Key: your-actual-api-key-value` (Phase 2 only)

**Request Body:**
Complete job specification as defined in [SCHEMA.md](SCHEMA.md).

**Response (Success - 200):**

```json
{
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "submitted",
  "submittedAt": "2024-01-15T10:25:00.000000+00:00",
  "updatedAt": "2024-01-15T10:30:45.123456+00:00",
  "completedAt": null,
  "processingTime": null,
  "output": {
    "url": null,
    "urlExpiresAt": null,
    "s3Uri": null,
    "duration": null,
    "size": null
  },
  "jobInfo": {
    "projectId": "demo_project",
    "title": "Welcome Video",
    "tags": ["demo"]
  },
  "error": null
}
```

**Response Fields:**

- `jobId` - Unique identifier for the job
- `status` - Current job status: "submitted", "processing", "completed", "failed"
- `submittedAt` - ISO 8601 timestamp when job was submitted (UTC)
- `updatedAt` - ISO 8601 timestamp of last status update (UTC)
- `completedAt` - ISO 8601 completion timestamp (null until completed)
- `processingTime` - Duration in seconds (null until completed)
- `output` - Output information object (fields are null until completed)
- `jobInfo` - Original job information from request
- `error` - Error message (null unless failed)

**Error Responses:**

**400 Bad Request:**

```json
{
  "error": "Validation failed",
  "details": "timeline cannot be empty"
}
```

**403 Forbidden:**

```json
{
  "message": "Forbidden"
}
```

**429 Too Many Requests (Phase 2 only):**

```json
{
  "message": "Too Many Requests"
}
```

**500 Internal Server Error:

```json
{
  "error": "Internal server error",
  "details": "Failed to queue job"
}
```

### Get Job Status

Retrieve the current status of a job.

**Endpoint:** `GET /status/{jobId}`

**Path Parameters:**

- `jobId` - The job ID returned from submit endpoint

**Response (Success - 200):**

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
  "jobInfo": {
    "projectId": "demo_project",
    "title": "Welcome Video",
    "tags": ["demo"]
  },
  "error": null
}
```

**Output Object (when completed):**

- `url` - Pre-signed download URL (expires in 24 hours)
- `urlExpiresAt` - ISO 8601 expiration time for download URL
- `s3Uri` - Internal S3 URI reference
- `duration` - Video length in seconds
- `size` - File size in bytes

**Error Responses:**

**403 Forbidden:**

```json
{
  "message": "Forbidden"
}
```

**404 Not Found:**

```json
{
  "error": "Job not found",
  "details": "Job ID does not exist"
}
```

**429 Too Many Requests (Phase 2 only):**

```json
{
  "message": "Too Many Requests"
}
```

**500 Internal Server Error:

```json
{
  "error": "Internal server error",
  "details": "Failed to retrieve job status"
}
```

## Job Status Flow

1. **submitted** - Job accepted and queued for processing
2. **processing** - Video generation in progress
3. **completed** - Video successfully generated and available for download
4. **failed** - Processing failed (check `error` field for details)

## Rate Limits (Phase 2 Only)

When deployed with Phase 2, API key-based rate limiting is enforced:

- **Rate Limit:** 2 requests per second
- **Burst Limit:** 5 requests (short bursts allowed)
- **Daily Quota:** 50 requests per day

**Rate Limit Headers:**
API Gateway returns standard rate limiting headers in responses.

**Exceeding Limits:**
- Returns `429 Too Many Requests` status
- Retry after the rate limit window resets

## Examples

### Submit Job Using Sample Specs

```bash
# Phase 1 (No authentication)
curl -X POST https://your-api-url/submit \
  -H "Content-Type: application/json" \
  -d @samples/production/00_api_demo_video.spec.json

# Phase 2 (With authentication)
curl -X POST https://your-api-url/submit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-actual-api-key" \
  -d @samples/production/00_api_demo_video.spec.json
```

### Submit Social Media Short with Sound Effects

```bash
# Phase 1 (No authentication)
curl -X POST https://your-api-url/submit \
  -H "Content-Type: application/json" \
  -d @samples/production/01_short_video.spec.json

# Phase 2 (With authentication)
curl -X POST https://your-api-url/submit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-actual-api-key" \
  -d @samples/production/01_short_video.spec.json
```

### Submit Multi-language TTS Video

```bash
# Phase 1 (No authentication)
curl -X POST https://your-api-url/submit \
  -H "Content-Type: application/json" \
  -d @samples/production/02_explainer_video_french.spec.json

# Phase 2 (With authentication)
curl -X POST https://your-api-url/submit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-actual-api-key" \
  -d @samples/production/02_explainer_video_french.spec.json
```

### Check Job Status

```bash
# Phase 1 (No authentication)
curl https://your-api-url/status/550e8400-e29b-41d4-a716-446655440000

# Phase 2 (With authentication)
curl https://your-api-url/status/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: your-actual-api-key"
```

## Error Handling

- **4xx errors** indicate client issues (invalid request format, missing fields)
- **5xx errors** indicate server issues (processing failures, infrastructure problems)
- Always check the `error` field in job status responses for failure details
- Failed jobs remain in the system for 7 days before automatic cleanup

## Webhooks

When a job completes (success or failure), Auto-Vid can send a webhook notification. The webhook payload uses the same format as the status API response. See [SCHEMA.md](SCHEMA.md#notifications) for webhook configuration details.
