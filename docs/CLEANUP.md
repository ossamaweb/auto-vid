# Cleanup Guide

## ⚠️ Important: Cost Management

**This will permanently delete all your videos and data. Download any important outputs first.**

## Safe Cleanup Process

```bash
# 1. Replace with your actual stack name (from sam deploy --guided)
STACK_NAME="auto-vid-demo"

# 2. Download any important videos first (optional)
# Replace with your actual bucket name from deployment output
BUCKET_NAME="auto-vid-s3-bucket-demo-123456789012"
mkdir -p ./downloaded-videos
aws s3 sync s3://$BUCKET_NAME/outputs/ ./downloaded-videos/

# 3. Delete stack
echo "Deleting stack: $STACK_NAME"
aws cloudformation delete-stack --stack-name $STACK_NAME

# 4. Wait for completion (optional)
aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME
echo "✅ Stack deleted successfully"
```

## Manual Cleanup (if automatic fails)

```bash
# If stack deletion fails, clean up manually:

# 1. Empty S3 bucket (replace with your actual bucket name)
aws s3 rm s3://auto-vid-s3-bucket-demo-123456789012 --recursive
aws s3 rb s3://auto-vid-s3-bucket-demo-123456789012

# 2. Delete ECR repository
aws ecr delete-repository --repository-name auto-vid-videoprocessorfunction --force

# 3. Retry stack deletion
aws cloudformation delete-stack --stack-name auto-vid-demo
```

## Verify Complete Cleanup

```bash
# Check for any remaining resources
echo "Checking for remaining Auto-Vid resources..."

# Check if stack still exists
if aws cloudformation describe-stacks --stack-name auto-vid-demo 2>/dev/null; then
  echo "❌ Stack still exists"
else
  echo "✅ Stack deleted successfully"
fi

# Check S3 buckets
aws s3 ls | grep auto-vid || echo "✅ No S3 buckets found"

echo "\n🎉 Cleanup verification complete!"
```

## What Gets Deleted

When you delete the CloudFormation stack, the following resources are automatically removed:

- **Lambda functions** - All three functions (Submit, Status, VideoProcessor)
- **S3 bucket** - Including all stored videos and assets
- **ECR repository** - Container images
- **SQS queue** - Job processing queue
- **DynamoDB table** - Job status tracking
- **API Gateway** - REST API endpoints
- **IAM roles and policies** - All associated permissions

## Cost Monitoring

To avoid unexpected charges:

1. **Set up billing alerts** in AWS Console
2. **Monitor CloudWatch metrics** for Lambda invocations
3. **Check S3 storage usage** regularly
4. **Use the cleanup script** when done testing
5. **Consider using AWS Cost Explorer** for detailed cost analysis