#!/usr/bin/env python3
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables for local testing
load_dotenv()

# Add src to path for imports
sys.path.append("src/video_processor")
from video_processor import VideoProcessor


def test_video_processing():
    """Test video processor locally with sample job spec"""

    # Load sample job spec
    with open("sample_input/advanced_job_spec.json", "r") as f:
        job_spec = json.load(f)

    try:
        # Use local tmp directory in repo
        processor = VideoProcessor(temp_dir="./tmp")
        result_url = processor.process_video_job(job_spec)
        print(f"✅ Video processing completed successfully!")
        print(f"📁 Result URL: {result_url}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    print("🎬 Testing Auto-Vid Video Processor...")
    success = test_video_processing()
    sys.exit(0 if success else 1)
