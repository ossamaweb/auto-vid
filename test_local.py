#!/usr/bin/env python3
import json
import sys
import os
import uuid
import logging
from dotenv import load_dotenv


# Add paths for imports
sys.path.append("src")
sys.path.append("layers/auto-vid-shared")
from video_processor.video_processor import VideoProcessor
from job_validator import validate_job_spec

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Load environment variables for local testing
load_dotenv()


def test_video_processing():
    """Test video processor locally with sample job spec"""

    job_id = str(uuid.uuid4())

    # Load sample job spec
    with open("sample_input/long_job_spec.json", "r") as f:
        job_spec_dict = json.load(f)

    try:
        # Validate job spec
        job_spec = validate_job_spec(job_spec_dict)

        # Use local tmp directory in repo
        processor = VideoProcessor(temp_dir="./tmp")
        result_url = processor.process_video_job(job_id, job_spec)
        print("✅ Video processing completed successfully!")
        print(f"📁 Result URL: {result_url}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    print("🎬 Testing Auto-Vid Video Processor...")
    success = test_video_processing()
    sys.exit(0 if success else 1)
