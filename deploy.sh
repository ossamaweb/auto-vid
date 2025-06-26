#!/bin/bash

# Auto-Vid Simplified Deployment Script
set -e

STACK_NAME=${1:-auto-vid}
REGION=${2:-us-east-1}

echo "🚀 Deploying Auto-Vid to AWS..."
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo ""

# Build and deploy with SAM
echo "📦 Building container and deploying infrastructure..."
sam build
sam deploy --stack-name $STACK_NAME --region $REGION --capabilities CAPABILITY_IAM --resolve-s3

# Get outputs for user
echo ""
echo "🔍 Getting deployment information..."
API_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`SubmitJobApi`].OutputValue' \
  --output text)

BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`AutoVidBucket`].OutputValue' \
  --output text)

echo ""
echo "✅ Deployment complete!"
echo "📡 API Gateway URL: $API_URL"
echo "🪣 S3 Bucket: $BUCKET_NAME"
echo ""
echo "🧪 Test your deployment:"
echo "curl -X POST $API_URL -H 'Content-Type: application/json' -d '{\"assets\":{\"video\":{\"id\":\"main\",\"source\":\"s3://$BUCKET_NAME/assets/video.mp4\"},\"audio\":[]},\"timeline\":[],\"output\":{\"filename\":\"test.mp4\"}}'"