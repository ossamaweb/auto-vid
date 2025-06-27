# Auto-Vid: Serverless Video Processing Platform

A production-ready serverless video enrichment pipeline that uses a declarative JSON format to automatically add AI-powered TTS, music, and sound effects to video.

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Architecture](#️-architecture)
- [Quick Start](#-quick-start)
- [Job Specification](#-job-specification)
- [Business Problems Solved](#-business-problems-solved)
- [Use Cases](#-use-cases)
- [Development](#️-development)
- [Configuration](#-configuration)
- [Performance & Limits](#-performance--limits)
- [Production Ready](#-production-ready)
- [Cleanup](#-cleanup)

## ✨ Key Features

- **🎬 Professional Video Processing** - MoviePy-powered video editing with precise timeline control
- **🗣️ AI Text-to-Speech** - AWS Polly with 90+ voices, multiple engines, and SSML support
- **🎵 Smart Audio Mixing** - Background music with crossfading, ducking, and volume control
- **🔔 Webhook Notifications** - Real-time job completion notifications with retry logic
- **☁️ Managed S3 Storage** - Automatic bucket creation with organized asset management
- **🔒 Production Security** - IAM least-privilege, input validation, and error handling
- **📊 Scalable Architecture** - SQS queuing, Lambda concurrency, and retry logic

## 🏗️ Architecture

### Core Components

- **Submit Job API** - Validates job specs and queues processing via SQS
- **Video Processor** - Handles video generation with MoviePy and AWS Polly
- **Status API** - Returns job progress and completion status
- **Managed S3 Bucket** - Automatic storage for assets and outputs
- **Shared Layer** - Pydantic models and validation logic

### AWS Services Used

- **Lambda** - Serverless compute with 15-minute timeout support
- **API Gateway** - RESTful API endpoints
- **SQS** - Reliable job queuing with dead letter handling
- **S3** - Asset storage with lifecycle management
- **Polly** - Neural and generative text-to-speech
- **CloudFormation** - Infrastructure as Code via SAM

## 🚀 Quick Start

### ⚠️ Cost Warning

**This application will incur AWS charges** when deployed and used. Costs include:

- **Lambda execution** - Video processing (up to 15 minutes per job)
- **S3 storage** - Input assets and output videos
- **ECR storage** - Container image (~360MB)
- **API Gateway** - API requests
- **SQS** - Message processing
- **Polly** - Text-to-speech generation

Monitor your AWS billing dashboard and set up billing alerts. See the [Cleanup](#-cleanup) section to delete resources when done.

### Prerequisites

- **AWS CLI** configured with appropriate permissions
- **SAM CLI** installed
- **Python 3.12+**

#### AWS Permissions for Local Testing

Your AWS credentials need:

- `AmazonPollyFullAccess` (for TTS generation)
- `AmazonS3FullAccess` (for asset download/upload)
- Or `PowerUserAccess` for comprehensive access

For deployment permissions, see [SAM Prerequisites](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/prerequisites.html).

```bash
# Verify your setup
aws sts get-caller-identity
aws polly describe-voices --region us-east-1
```

### Deploy to AWS

```bash
# Clone repository
git clone https://github.com/ossamaweb/auto-vid.git
cd auto-vid

# Build and deploy
sam build
sam deploy --guided

# Answer 'Y' when asked: "Create managed ECR repositories for all functions?"
# SAM will build, push container, and deploy everything automatically

# For subsequent deployments (settings saved in samconfig.toml)
sam build
sam deploy
```

### Submit Your First Job

```bash
# Simple background music example
curl -X POST https://your-api-url/submit \
  -H "Content-Type: application/json" \
  -d '{
    "assets": {
      "video": {"id": "main", "source": "s3://your-bucket/video.mp4"},
      "audio": [{"id": "music", "source": "s3://your-bucket/music.mp3"}]
    },
    "backgroundMusic": {"playlist": ["music"], "volume": 0.3},
    "timeline": [],
    "output": {"filename": "result.mp4"},
    "notifications": {
      "webhook": {
        "url": "https://your-app.com/webhook",
        "headers": {"Authorization": "Bearer your-token"}
      }
    }
  }'

# Check status
curl https://your-api-url/status/{jobId}
```

## 📋 Job Specification

Auto-Vid uses a declarative JSON format for video generation:

### Basic Structure

```json
{
  "assets": {
    "video": { "id": "main_video", "source": "s3://bucket/video.mp4" },
    "audio": [
      { "id": "bgm", "source": "s3://bucket/music.mp3" },
      { "id": "sfx", "source": "s3://bucket/sound.wav" }
    ]
  },
  "backgroundMusic": {
    "playlist": ["bgm"],
    "volume": 0.3,
    "crossfadeDuration": 2.0
  },
  "timeline": [
    {
      "start": 0,
      "type": "tts",
      "data": {
        "text": "Welcome to Auto-Vid!",
        "providerConfig": {
          "voiceId": "Joanna",
          "engine": "neural"
        },
        "duckingLevel": 0.2
      }
    }
  ],
  "output": { "filename": "my-video.mp4" },
  "notifications": {
    "webhook": {
      "url": "https://your-app.com/webhook/complete",
      "headers": { "Authorization": "Bearer token" },
      "metadata": { "project": "demo", "priority": "high" }
    }
  }
}
```

See [SCHEMA.md](SCHEMA.md) for complete documentation.

### Advanced Features

- **Empty Timeline Support** - Create videos with just background music
- **Audio Ducking** - Automatically lower background music during speech
- **Multiple TTS Engines** - Standard, neural, long-form, and generative
- **SSML Support** - Advanced speech markup for pronunciation control
- **Crossfading** - Smooth transitions between background music tracks
- **Webhook Notifications** - Real-time completion notifications with custom headers and metadata

#### Webhook Payload

When jobs complete, webhooks receive a JSON payload:

```json
{
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "timestamp": "2024-01-15T10:30:45.123456+00:00",
  "processingTime": 127.45,
  "output": {
    "url": "s3://auto-vid-bucket/outputs/my-video.mp4",
    "duration": 90.2,
    "size": 15728640
  },
  "error": null,
  "metadata": {
    "project": "demo",
    "priority": "high"
  }
}
```

See [SCHEMA.md](SCHEMA.md#_payload_fields) for complete webhook payload documentation.

## 💼 Business Problems Solved

Auto-Vid directly addresses several major pain points in modern content creation:

1. **High Cost and Complexity of Video Production** - Eliminates the need for expensive video editing software (like Adobe Premiere Pro or Final Cut Pro) and the specialized skills required to use them for common, repetitive tasks.

2. **Slow Content Turnaround Times** - Replaces a manual, multi-hour editing process with an automated workflow that can generate a finished video in minutes. This drastically increases content velocity.

3. **Lack of Scalability** - A human editor can only work on one video at a time. This serverless architecture can process dozens or hundreds of videos in parallel, allowing businesses to scale their video output without a linear increase in cost or personnel.

4. **Inconsistent Branding and Quality** - Manual editing can lead to variations in audio levels, music choices, and overall feel. By using a configuration file (the JSON), your solution ensures every video adheres to a consistent, high-quality brand template.

5. **The "Content Treadmill"** - Provides a powerful tool for marketing and social media teams to efficiently create the high volume of content needed to stay relevant on platforms like TikTok, Instagram Reels, and YouTube Shorts.

## 🎯 Use Cases

### 1. Automated Social Media Video Production

**Scenario:** A marketing team needs to create 5-10 short-form videos per week for Instagram and TikTok. The format is always the same: a short clip with a voiceover, background music, and a "swoosh" sound effect for transitions.

**Problem:** Manually creating these videos is tedious, repetitive, and takes up a significant portion of a social media manager's time.

**Solution:** The manager simply provides the video clip and a simple JSON file with the voiceover text for each new video. The system automatically generates the ready-to-post video, complete with music and SFX, freeing up the team to focus on strategy and community engagement.

### 2. Dynamic E-commerce Product Demos

**Scenario:** An online retailer has thousands of products. They want to create a short video for each product page that highlights key features.

**Problem:** It is financially and logistically impossible to hire a video team to create and narrate thousands of unique videos.

**Solution:** The company can use a template video and programmatically generate a JSON file for each product from their database. The TTS data would be populated with product features. This allows them to automatically create a unique, narrated video for every single item in their catalog.

### 3. Content Localization at Scale

**Scenario:** A global company creates a training video in English. They need to distribute the same video to their teams in Germany, Japan, and Spain.

**Problem:** Hiring voice actors and video editors for multiple languages is slow and extremely expensive.

**Solution:** The company uses the exact same video file. They create three different JSON files, one for each language, with the script translated. By changing the TTS voice to German, Japanese, or Spanish Polly voices, they can generate professionally narrated versions for each region in a fraction of the time and cost.

### 4. Automated Real Estate Video Tours

**Scenario:** A real estate agency takes raw video walkthroughs of their properties. They need to add a professional voiceover describing each room and some pleasant background music.

**Problem:** Agents are not video editors. Outsourcing this work is costly and adds days to the time it takes to get a listing online.

**Solution:** An agent can upload their phone video and fill out a simple web form that generates the JSON file (e.g., "At 15 seconds, say 'Here we have the spacious, open-concept kitchen'"). The system produces a polished, ready-to-use video tour that can be immediately added to the listing.

### 5. Rapid News Clip Generation

**Scenario:** A digital news outlet needs to quickly publish video clips about breaking news. They have stock footage and a script from a journalist.

**Problem:** In a 24/7 news cycle, the time it takes for a video editor to become available and render a video can mean missing the peak moment of interest.

**Solution:** A journalist can submit their script into a system that generates the JSON. The system can use a standard "news-style" Polly voice to narrate the script over stock footage, add the channel's theme music, and publish a video to the web within minutes of the story breaking.

## 🛠️ Development

### Local Development Setup

#### For Python Script Testing

```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Copy environment template and add your AWS credentials
cp .env.example .env
# Edit .env with your AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, etc.

# Test AWS Polly locally
python3 test_tts_local.py english  # or spanish, french, arabic, all

# Test video processing locally
python3 test_local.py
```

#### For Container Testing

**Option 1: Use Local Output (Recommended for testing)**

```bash
# Create output directory
mkdir -p ./output

# Modify your event file to use local destination:
# "output": {"destination": "./output", "filename": "test-video.mp4"}

# Run with volume mount
sam local invoke videoprocessorfunction -e events/event-process-job.json \
  --docker-volume-basedir $(pwd)

# Check output
ls -la ./output/
```

**Option 2: Use S3 Output (Requires deployed resources)**

```bash
# Create env.json with actual AWS resources
cat > env.json << EOF
{
  "videoprocessorfunction": {
    "AWS_ACCESS_KEY_ID": "your-access-key",
    "AWS_SECRET_ACCESS_KEY": "your-secret-key",
    "AWS_DEFAULT_REGION": "us-east-1",
    "AUTO_VID_BUCKET": "auto-vid-your-stack-name-your-account-id"
  }
}
EOF

# Find your actual bucket name (after deployment)
aws s3 ls | grep auto-vid
# OR
aws cloudformation describe-stacks --stack-name your-stack-name \
  --query 'Stacks[0].Outputs[?OutputKey==`AutoVidBucket`].OutputValue' --output text

# Run with environment variables
sam local invoke videoprocessorfunction -e events/event-process-job.json \
  --env-vars env.json
```

### Troubleshooting Local Development

**CloudFormation References Don't Work Locally**

- `AUTO_VID_BUCKET: !Ref AutoVidBucket` becomes literal `"AutoVidBucket"` in local testing
- Use actual bucket names in `env.json` for S3 testing
- Or use local destinations for simpler testing

**Missing AWS Credentials**

- Ensure `.env` file has valid AWS credentials for Python scripts
- Ensure `env.json` has valid credentials for container testing
- Test with: `aws sts get-caller-identity`

**Import Errors**

- Run from project root directory
- Ensure all `__init__.py` files are present
- Check Python path with `python3 -c "import sys; print(sys.path)"`

### Advanced Container Development

```bash
# Build container with SAM
sam build

# Debug container interactively
docker run -it --entrypoint /bin/bash videoprocessorfunction:latest

# Inside container, explore the environment
ls -la /var/task/
echo $AUTO_VID_BUCKET
python3 -c "import video_processor; print('Import successful')"

# Clean up dangling images
docker image prune -f
```

### SAM Deployment Process

SAM handles the entire deployment automatically:

1. **Container Build** - `sam build` creates optimized Docker image (~360MB)
2. **Infrastructure Deployment** - `sam deploy` creates all AWS resources
3. **Automatic ECR Management** - SAM creates repository, pushes image, updates Lambda
4. **Configuration Persistence** - Settings saved in `samconfig.toml` for future deployments

**Key features:**

- **Multi-stage Docker build** - Optimized container size
- **Managed ECR repositories** - No manual Docker/ECR commands needed
- **Guided deployment** - Interactive prompts for first-time setup
- **One-command updates** - Simple `sam deploy` for subsequent deployments

### Project Structure

```
├── src/
│   ├── submit_job/           # Job submission API
│   ├── get_status/           # Status checking API
│   └── video_processor/      # Core video processing
│       ├── video_processor.py
│       ├── asset_manager.py  # S3 integration
│       └── tts_generator.py  # AWS Polly integration
├── layers/auto-vid-shared/   # Shared Pydantic models
│   ├── job_spec_models.py
│   ├── job_validator.py
│   └── polly_constants.py    # Voice/language definitions
├── sample_input/             # Example job specifications
├── template.yaml             # SAM infrastructure
└── SCHEMA.md                 # Complete API documentation
```

## 🔧 Configuration

### Environment Variables

- `AUTO_VID_BUCKET` - Managed S3 bucket name (auto-configured)
- `AWS_LAMBDA_FUNCTION_NAME` - Detected automatically in Lambda
- `WEBHOOK_MAX_HEADERS_SIZE` - Maximum webhook headers size in bytes (default: 1024)
- `WEBHOOK_MAX_METADATA_SIZE` - Maximum webhook metadata size in bytes (default: 1024)

### Resource Naming

All AWS resources use consistent naming:

- S3 Bucket: `auto-vid-{stack-name}-{account-id}`
- SQS Queue: `auto-vid-jobs-{stack-name}-{account-id}`
- Lambda Layer: `auto-vid-shared-{stack-name}-{account-id}`

### Managed S3 Bucket

- **Automatic Creation** - No manual S3 setup required
- **Organized Structure** - `/assets/` and `/outputs/` prefixes
- **Security** - Private bucket with proper IAM policies
- **Flexibility** - Can override with custom S3 URIs

## 📊 Performance & Limits

### Lambda Configuration

**API Functions (Submit/Status):**

- **Memory**: 256-512 MB (lightweight JSON processing)
- **Timeout**: 30-60 seconds (fast API responses)
- **Storage**: Default 512 MB (no file processing needed)

**Video Processor:**

- **Memory**: 10,240 MB (maximum available for intensive processing)
- **Timeout**: 15 minutes (maximum allowed)
- **Storage**: 10 GB ephemeral storage (large video files)
- **Container Size**: ~360MB (optimized multi-stage build)

**Benefits:**

- **Cost Optimized** - API functions use minimal resources
- **Performance Optimized** - Video processor uses maximum resources
- **Right-sized** - Each function configured for its specific workload

### Supported Formats

- **Video Input**: MP4, AVI, MOV, MKV
- **Audio Input**: MP3, WAV, M4A, FLAC
- **Video Output**: MP4 with H.264/AAC

## 🏆 Production Ready

- **✅ Input Validation** - Comprehensive Pydantic models
- **✅ Error Handling** - Retry logic and detailed error messages
- **✅ Security** - IAM least privilege and input sanitization
- **✅ Monitoring** - CloudWatch logs and metrics
- **✅ Scalability** - SQS queuing and Lambda concurrency
- **✅ Cost Optimization** - Pay-per-use serverless architecture

Built for the **AWS Lambda Hackathon** - demonstrating enterprise-grade serverless video processing! 🚀

## 🧹 Cleanup

### Delete AWS Stack

**To avoid ongoing charges, delete the stack when done:**

```bash
# Delete the entire stack and all resources
aws cloudformation delete-stack --stack-name <your-stack-name>

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name <your-stack-name>

# Verify deletion
aws cloudformation describe-stacks --stack-name <your-stack-name>
# Should return: "Stack with id <stack-name> does not exist"
```

**What gets deleted:**

- Lambda functions
- S3 bucket (and all contents)
- ECR repository (and container images)
- SQS queue
- API Gateway
- IAM roles and policies

**⚠️ Warning**: This permanently deletes all your videos and data. Download any important outputs before deletion.

### Manual Cleanup (if needed)

```bash
# If stack deletion fails, manually delete resources:

# Empty S3 bucket first
aws s3 rm s3://auto-vid-<stack-name>-<account-id> --recursive

# Delete ECR images
aws ecr batch-delete-image \
  --repository-name <repository-name> \
  --image-ids imageTag=latest

# Then retry stack deletion
aws cloudformation delete-stack --stack-name <your-stack-name>
```
