#!/bin/bash

# Auto-Vid Container Deployment Script
set -e

STACK_NAME=${1:-auto-vid}
REGION=${2:-us-east-1}

echo "🚀 Deploying Auto-Vid to AWS..."
echo "Stack: $STACK_NAME"
echo "Region: $REGION"

# Step 1: Deploy infrastructure
echo "📦 Building and deploying infrastructure..."
sam build
sam deploy --stack-name $STACK_NAME --region $REGION --capabilities CAPABILITY_IAM --resolve-s3

# Step 2: Get ECR repository URI
echo "🔍 Getting ECR repository URI..."
ECR_REPO=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ECRRepository`].OutputValue' \
  --output text)

if [ -z "$ECR_REPO" ]; then
  echo "❌ Failed to get ECR repository URI"
  exit 1
fi

echo "📍 ECR Repository: $ECR_REPO"

# Step 3: Build and push container image
echo "🐳 Building container image..."
docker build -t auto-vid-processor .

echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO

echo "🏷️ Tagging and pushing image..."
docker tag auto-vid-processor:latest $ECR_REPO:latest
docker push $ECR_REPO:latest

# Step 4: Update Lambda function
echo "⚡ Updating Lambda function..."
FUNCTION_NAME=$(aws cloudformation describe-stack-resources \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'StackResources[?LogicalResourceId==`VideoProcessorFunction`].PhysicalResourceId' \
  --output text)

aws lambda update-function-code \
  --function-name $FUNCTION_NAME \
  --image-uri $ECR_REPO:latest \
  --region $REGION

# Step 5: Get API Gateway URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`SubmitJobApi`].OutputValue' \
  --output text)

echo ""
echo "✅ Deployment complete!"
echo "📡 API Gateway URL: $API_URL"
echo "🪣 S3 Bucket: auto-vid-$STACK_NAME-$(aws sts get-caller-identity --query Account --output text)"
echo ""
echo "Test your deployment:"
echo "curl -X POST $API_URL -H 'Content-Type: application/json' -d @sample_input/simple_job.json"