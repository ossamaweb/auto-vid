#!/usr/bin/env python3
# Usage: python test_tts_local.py [language]
# Languages: english (default), spanish, french, arabic, all
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.append("src")

from video_processor.tts_generator import TTSGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def test_language(tts, lang_config, output_dir):
    """Test TTS for a specific language"""
    try:
        output_file = os.path.join(
            output_dir, f"test_{lang_config['name'].lower()}.mp3"
        )
        result = tts.generate_speech(
            lang_config["text"],
            output_file,
            engine=lang_config["engine"],
            voice_id=lang_config["voice"],
            language_code=lang_config.get("code"),
        )

        size = os.path.getsize(result) if os.path.exists(result) else 0
        print(f"✅ {lang_config['name']}: {size} bytes")
        return True

    except Exception as e:
        print(f"❌ {lang_config['name']}: {str(e)}")
        return False


def test_tts():
    """Test TTS generator with multiple languages"""
    languages = {
        "english": {
            "name": "English",
            "text": "Hello! This is a test of Amazon Polly.",
            "voice": "Joanna",
            "code": "en-US",
        },
        "spanish": {
            "name": "Spanish",
            "text": "Hola! Esta es una prueba de Amazon Polly.",
            "voice": "Lupe",
            "code": "es-US",
        },
        "french": {
            "name": "French",
            "text": "Bonjour! Ceci est un test d'Amazon Polly.",
            "voice": "Matthew",
            "engine": "generative",
            "code": "fr-FR",
        },
        "arabic": {
            "name": "Arabic",
            "text": "مرحبا! هذا اختبار لأمازون بولي.",
            "voice": "Hala",
            "engine": "neural",
            "code": "ar-AE",
        },
    }

    # Get language from command line or default to all
    lang_arg = sys.argv[1] if len(sys.argv) > 1 else "english"

    try:
        tts = TTSGenerator()
        output_dir = "./media/outputs/.aws-polly"
        os.makedirs(output_dir, exist_ok=True)

        if lang_arg == "all":
            print("🎤 Testing all languages...")
            results = [
                test_language(tts, config, output_dir) for config in languages.values()
            ]
            success = all(results)
        elif lang_arg in languages:
            print(f"🎤 Testing {languages[lang_arg]['name']}...")
            success = test_language(tts, languages[lang_arg], output_dir)
        else:
            print(f"❌ Unknown language: {lang_arg}")
            print(f"Available: {', '.join(languages.keys())}, all")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

    return success


if __name__ == "__main__":
    success = test_tts()
    sys.exit(0 if success else 1)
