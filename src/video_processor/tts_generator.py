import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import logging

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


class TTSGenerator:
    def __init__(self):
        """
        Initialize the TTS Generator with Amazon Polly
        Uses Lambda's built-in IAM role for authentication
        """
        try:
            self.polly_client = boto3.client("polly", region_name="us-east-1")
            logger.info("Successfully initialized Polly client in us-east-1")
        except Exception as e:
            logger.error(f"Failed to initialize AWS Polly client: {str(e)}")
            raise

    def generate_speech(
        self,
        text,
        output_path,
        voice_id="Joanna",
        engine="neural",
        language_code=None,
        text_type="text",
    ):
        """
        Generate speech from text using Amazon Polly and save as MP3

        Args:
            text (str): The text to convert to speech
            output_path (str): Path where to save the MP3 file
            voice_id (str): The Polly voice ID to use (default: Joanna)
            engine (str): The engine type to use ('neural' or 'standard')
            language_code (str): Optional language code
            text_type (str): Text type ('text' or 'ssml')

        Returns:
            str: Path to the generated audio file
        """
        try:
            # Build synthesis parameters
            params = {
                "Text": text,
                "OutputFormat": "mp3",
                "VoiceId": voice_id,
                "Engine": engine,
                "TextType": text_type,
            }

            if language_code:
                params["LanguageCode"] = language_code

            # Request speech synthesis
            response = self.polly_client.synthesize_speech(**params)

            # Save the audio stream to file
            if "AudioStream" in response:
                with closing(response["AudioStream"]) as stream:
                    try:
                        # Ensure the directory exists
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)

                        # Write the audio stream to file
                        with open(output_path, "wb") as file:
                            file.write(stream.read())

                        logger.info(f"Successfully generated speech at: {output_path}")
                        return output_path

                    except IOError as error:
                        logger.error(f"Error writing audio file: {str(error)}")
                        raise
            else:
                logger.error("No AudioStream found in the response")
                raise Exception("No AudioStream in response")

        except (BotoCoreError, ClientError) as error:
            logger.error(f"Error generating speech: {str(error)}")
            raise
