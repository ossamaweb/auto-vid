# Auto-Vid Serverless Video Processing

A serverless video processing application built with AWS SAM that automatically generates videos with TTS, background music, and sound effects using a declarative JSON job specification.

## 🏗️ Architecture

- **Submit Job API** - Accepts video processing jobs and queues them
- **Video Processor** - Processes videos using MoviePy v2.1.2, AWS Polly TTS, and advanced audio mixing
- **Status API** - Returns job status and progress

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
python test_local.py
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
  -d @sample_input/job_spec.json
```

## 📋 Job Specification

The heart of Auto-Vid is the **Video Job Specification** - a declarative JSON format that describes:
- **Assets**: Video and audio files to use
- **Timeline**: TTS, sound effects, and background music events
- **Output**: Destination and filename

See `SCHEMA.md` for complete documentation and `sample_input/job_spec.json` for examples.

## 🧪 Testing

### Local Testing
```bash
# Test with sample job spec
python test_local.py

# Test individual Lambda functions
sam local invoke VideoProcessorFunction -e events/event-process-job.json
```

### Container Deployment
For better performance with MoviePy:
```bash
docker build -t auto-vid .
sam deploy --image-repository your-ecr-repo
```

## 🎯 Features

- **MoviePy v2.1.2** - Latest video processing capabilities
- **AWS Polly TTS** - High-quality text-to-speech
- **Smart Audio Mixing** - Background music with ducking
- **Asset Management** - S3 and HTTP/HTTPS support
- **Serverless Scale** - Handles multiple jobs concurrently

## 🏆 AWS Lambda Hackathon

Built for the AWS Lambda Hackathon - showcasing serverless video processing at scale!