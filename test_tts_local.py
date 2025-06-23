#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Load environment variables for local testing
load_dotenv()

# Add src to path for imports
sys.path.append('src/video_processor')

from tts_generator import TTSGenerator

def test_tts():
    """Test TTS generator locally"""
    try:
        tts = TTSGenerator()
        text = "Hello! This is a test of the Amazon Polly text to speech system."
        output_file = "test_speech.mp3"
        
        result = tts.generate_speech(text, output_file)
        print(f"Successfully generated speech at: {result}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_tts()