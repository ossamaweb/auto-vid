# Auto-Vid Serverless Video Processing

A serverless video processing application built with AWS SAM that automatically generates videos with TTS, background music, and sound effects using a declarative JSON job specification.

## 🏗️ Architecture

### Lambda Functions

- **Submit Job API** (`src/submit_job/`) - Validates job specs and queues them via SQS
- **Video Processor** (`src/video_processor/`) - Processes videos using MoviePy, AWS Polly TTS, and advanced audio mixing
- **Status API** - Returns job status and progress

### Shared Components

- **Job Spec Models** (`src/shared/job_spec_models.py`) - Pydantic models for validation
- **Job Validator** (`src/shared/job_validator.py`) - Centralized validation logic

### Key Features

- **Early Validation** - Job specs validated at submission to prevent processing invalid jobs
- **Hybrid Error Handling** - Distinguishes permanent vs transient failures for proper retry logic
- **Smart Audio Processing** - Background music with crossfading and ducking
- **Asset Management** - Supports S3, HTTP/HTTPS, and local file sources

## 🚀 Quick Start

### Local Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your AWS credentials
```

3. Test locally:

```bash
# Test full video processing pipeline
python3 test_local.py

# Test TTS generation only
python3 test_tts_local.py
```

### Serverless Deployment

1. Build and deploy:

```bash
sam build
sam deploy --guided
```

2. Submit a job:

```bash
curl -X POST https://your-api-gateway-url/submit \
  -H "Content-Type: application/json" \
  -d @sample_input/long_job_spec.json
```

3. Check job status:

```bash
curl https://your-api-gateway-url/status/{jobId}
```

## 📋 Job Specification

The heart of Auto-Vid is the **Video Job Specification** - a declarative JSON format that describes:

### Structure

- **metadata** (optional): Project info, title, tags
- **assets**: Video and audio files to use
  - **video**: Main background video
  - **audio**: Array of audio assets (music, SFX)
- **backgroundMusic** (optional): Continuous background audio with crossfading
- **timeline**: Timed events (TTS, audio clips) with ducking support
- **output**: Destination and encoding settings

### Validation

- **Pydantic Models** - Strong typing and validation
- **Early Validation** - Errors caught at submission time
- **Detailed Error Messages** - Clear feedback on validation failures

See `SCHEMA.md` for complete documentation and `sample_input/long_job_spec.json` for examples.

## 🧪 Testing

### Local Testing

```bash
# Test with sample job spec
python3 test_local.py

# Test TTS generation
python3 test_tts_local.py

# Test individual Lambda functions
sam local invoke SubmitJobFunction -e events/event-submit-job.json
sam local invoke VideoProcessorFunction -e events/event-process-job.json
```

### Container Deployment

Video Processor uses Docker for better MoviePy performance:

```bash
# Build container image
docker build -t auto-vid-processor ./src/video_processor

# Deploy with container image
sam deploy --guided
```

## 🎯 Features

### Video Processing

- **MoviePy** - Professional video editing capabilities
- **AWS Polly TTS** - High-quality text-to-speech with multiple voices
- **Smart Audio Mixing** - Background music with crossfading and ducking
- **Timeline Events** - Precise timing control for TTS and sound effects

### Architecture

- **Pydantic Validation** - Type-safe job specifications
- **Shared Modules** - Reusable validation and models across Lambda functions
- **Error Handling** - Distinguishes permanent vs transient failures
- **SQS Integration** - Reliable job queuing with retry logic

### Asset Management

- **Multi-source Support** - S3, HTTP/HTTPS, and local files
- **Automatic Downloads** - Assets fetched and cached during processing
- **Flexible Output** - S3 or local destination support

### Deployment

- **Serverless Scale** - Handles multiple jobs concurrently
- **Container Support** - Docker images for heavy processing workloads
- **AWS SAM** - Infrastructure as Code with easy deployment

## 📁 Project Structure

```
src/
├── shared/                    # Shared modules
│   ├── job_spec_models.py    # Pydantic models
│   └── job_validator.py      # Validation logic
├── submit_job/               # Job submission Lambda
│   └── app.py               # API handler with validation
├── video_processor/          # Video processing Lambda
│   ├── app.py               # SQS handler with error handling
│   ├── video_processor.py   # Core processing logic
│   ├── asset_manager.py     # Asset download/upload
│   └── tts_generator.py     # AWS Polly integration
sample_input/                 # Example job specifications
events/                       # Test events for SAM local
SCHEMA.md                    # Job specification documentation
```

## 🏆 AWS Lambda Hackathon

Built for the AWS Lambda Hackathon - showcasing serverless video processing at scale with modern Python practices and robust error handling!
