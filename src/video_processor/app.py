import json
import boto3
import logging
from video_processor import VideoProcessor

# Configure logging for Lambda
logging.basicConfig(level=logging.INFO)


def lambda_handler(event, context):
    try:
        for record in event["Records"]:
            message = json.loads(record["body"])
            job_id = message["jobId"]
            job_spec = message["jobSpec"]

            # Use /tmp for Lambda environment
            processor = VideoProcessor(temp_dir="/tmp")
            result_url = processor.process_video_job(job_id, job_spec)

            print(f"Job {job_id} processed successfully: {result_url}")

        return {"statusCode": 200, "body": json.dumps("Jobs processed successfully")}

    except Exception as e:
        print(f"Error processing job: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
