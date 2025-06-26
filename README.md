# Auto-Vid: Serverless Video Processing Platform

A production-ready serverless video processing application that automatically generates videos with AI-powered text-to-speech, background music, and sound effects using declarative JSON job specifications.

## ✨ Key Features

- **🎬 Professional Video Processing** - MoviePy-powered video editing with precise timeline control
- **🗣️ AI Text-to-Speech** - AWS Polly with 90+ voices, multiple engines, and SSML support
- **🎵 Smart Audio Mixing** - Background music with crossfading, ducking, and volume control
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

### Prerequisites

- AWS CLI configured with appropriate permissions
- SAM CLI installed
- Python 3.12+

### Deploy to AWS

#### Option 1: Automated Deployment (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd auto-vid

# One-command deployment
./deploy.sh <stack-name> <aws-region>
```

#### Option 2: Manual Deployment

```bash
# Step-by-step deployment for customization

# 1. Build and deploy (SAM handles container automatically)
sam build
sam deploy --guided

# Answer 'Y' when asked: "Create managed ECR repositories for all functions?"
# SAM will build, push container, and deploy everything automatically
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
    "output": {"filename": "result.mp4"}
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
  "output": { "filename": "my-video.mp4" }
}
```

### Advanced Features

- **Empty Timeline Support** - Create videos with just background music
- **Audio Ducking** - Automatically lower background music during speech
- **Multiple TTS Engines** - Standard, neural, long-form, and generative
- **SSML Support** - Advanced speech markup for pronunciation control
- **Crossfading** - Smooth transitions between background music tracks

See [SCHEMA.md](SCHEMA.md) for complete documentation.

## 🎯 Use Cases

### Content Creation

- **YouTube Videos** - Automated narration with background music
- **Podcasts** - Convert text to audio with intro/outro music
- **Educational Content** - Lecture videos with timed sound effects

### Business Applications

- **Product Demos** - Automated video generation from scripts
- **Training Materials** - Consistent narration across modules
- **Marketing Videos** - Scalable video content production

### Creative Projects

- **Storytelling** - Audio books with background ambiance
- **Game Development** - Automated cutscene generation
- **Social Media** - Batch video creation for campaigns

## 🛠️ Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Test locally (requires AWS credentials)
python test_local.py

# Test individual components
sam local invoke SubmitJobFunction -e events/submit-job.json
```

### Container Development

```bash
# Build container with SAM (recommended)
sam build

# Test container locally with SAM
sam local invoke videoprocessorfunction -e events/event-process-job.json

# Test with environment variables
# Create env.json:
# {
#   "videoprocessorfunction": {
#     "AWS_ACCESS_KEY_ID": "your-key",
#     "AWS_SECRET_ACCESS_KEY": "your-secret",
#     "AWS_DEFAULT_REGION": "us-east-1",
#     "AUTO_VID_BUCKET": "your-bucket"
#   }
# }
sam local invoke videoprocessorfunction -e events/event-process-job.json --env-vars env.json

# Debug container interactively
docker run -it --entrypoint /bin/bash videoprocessorfunction:latest
```

### Understanding the Deploy Script

The `deploy.sh` script simplifies deployment by leveraging SAM's managed ECR repositories:

1. **Container Build** - `sam build` creates optimized Docker image (~400-600MB)
2. **Infrastructure Deployment** - `sam deploy` creates all AWS resources
3. **Automatic ECR Management** - SAM creates repository, pushes image, updates Lambda
4. **Status Report** - Displays API URLs and resource names for testing

**Key optimizations:**
- **Multi-stage Docker build** - Reduces image size by 60-70%
- **Managed ECR repositories** - No manual Docker/ECR commands needed
- **Automatic container deployment** - SAM handles the entire container lifecycle
- **Environment variable support** - Easy local testing with env files

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

- **Memory**: 3008 MB for video processing
- **Timeout**: 15 minutes maximum
- **Storage**: 10 GB ephemeral storage
- **Container Size**: ~400-600MB (optimized multi-stage build)
- **Cold Start**: 5-10 seconds (optimized from 15-30 seconds)
- **Concurrency**: Configurable based on workload

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
