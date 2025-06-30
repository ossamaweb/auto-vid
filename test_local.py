#!/usr/bin/env python3
import json
import sys
import os
import uuid
import logging
from dotenv import load_dotenv


# Add paths for imports
sys.path.append("src/video_processor")
sys.path.append("layers/shared")
from webhook_notifier import WebhookNotifier
from video_processor import VideoProcessor
from asset_manager import AssetManager
from app import process_single_job


# Configure logging with colors
class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logging.getLogger().handlers[0].setFormatter(
    ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

# Load environment variables for local testing
load_dotenv()


class MockJobManager:
    """Mock JobManager for local testing"""

    def update_status(self, job_id, status, **kwargs):
        print(f"📊 Job {job_id}: Status updated to {status}")
        if kwargs:
            print(f"   Additional data: {kwargs}")

    def update_job_completion(
        self, job_id, status, processing_time, output, error=None
    ):
        print(f"✅ Job {job_id}: Completed with status {status}")
        print(f"   Processing time: {processing_time:.2f}s")
        if error:
            print(f"   Error: {error}")
        else:
            print(f"   Output: {output['url']}")


class MockWebhookNotifier:
    """Mock WebhookNotifier for local testing"""

    def create_payload(self, **kwargs):
        return kwargs

    def send_notification(self, config, payload):
        print(f"🔔 Webhook notification: {payload['status']}")
        if payload.get("error"):
            print(f"   Error: {payload['error']}")
        elif payload.get("output_url"):
            print(f"   Output URL: {payload['output_url']}")


class LocalJobProcessor:
    """Local version of JobProcessor for testing"""

    def __init__(self):
        self.job_manager = MockJobManager()
        self.video_processor = VideoProcessor(temp_dir="./tmp")
        self.asset_manager = AssetManager()
        self.webhook_notifier = WebhookNotifier()  # MockWebhookNotifier
        self.empty_output = {
            "url": None,
            "urlExpiresAt": None,
            "s3Uri": None,
            "duration": None,
            "size": None,
        }


def test_complete_pipeline(spec_file):
    """Test complete pipeline using process_single_job"""
    job_id = str(uuid.uuid4())

    # Load and prepare job spec for local testing
    with open(spec_file, "r") as f:
        job_spec_dict = json.load(f)

    try:
        # Create local processor
        processor = LocalJobProcessor()

        # Run complete pipeline
        print(f"🎬 Starting complete pipeline test for job {job_id}")
        result = process_single_job(processor, job_id, job_spec_dict)

        if result["status"] == "success":
            print("\n✅ Complete pipeline test PASSED!")
            print("   - Video processing: ✅")
            print("   - File upload: ✅")
            print("   - Job status update: ✅")
            print("   - Webhook notification: ✅")
            return True
        else:
            print(f"\n❌ Pipeline test FAILED: {result['status']}")
            return False

    except Exception as e:
        print(f"\n❌ Pipeline test ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Error: Please provide a job specification file")
        print("Usage: python3 test_local.py <spec_file>")
        print("Example: python3 test_local.py samples/local/00_api_demo_video.spec.json")
        sys.exit(1)
    
    spec_file = sys.argv[1]
    if not os.path.exists(spec_file):
        print(f"❌ Error: File '{spec_file}' not found")
        sys.exit(1)
    
    print(f"🎬 Testing Auto-Vid Complete Pipeline with {spec_file}...")

    # Test complete pipeline (recommended)
    success = test_complete_pipeline(spec_file)

    sys.exit(0 if success else 1)
