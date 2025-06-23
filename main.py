import os
import sys
import json
from pathlib import Path
from datetime import datetime
import requests
from urllib.parse import urlparse
from video_editor import add_audio
from tts_generator import TTSGenerator
from input import input
from input_shorts import input_shorts


def validate_actor_data(actor_data: dict, script_dir: Path) -> None:
    """
    Validate actor data and required files

    Args:
        actor_data (dict): Dictionary containing actor information
        script_dir (Path): Path to the script directory

    Raises:
        ValueError: If required fields are missing or SFX files don't exist
    """
    # Validate required fields
    required_fields = ["imdb_id", "name", "tts_data", "sfx_data"]
    missing_fields = [field for field in required_fields if field not in actor_data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    # Validate SFX files exist
    sfx_dir = script_dir / "lib" / "sfx"
    missing_sfx = []
    for sfx in actor_data["sfx_data"]:
        sfx_path = sfx_dir / sfx["data"]
        if not sfx_path.exists():
            missing_sfx.append(sfx["data"])

    if missing_sfx:
        raise ValueError(f"Missing SFX files: {', '.join(missing_sfx)}")


def setup_project_folder(actor_data: dict, script_dir: Path) -> str:
    """
    Set up a project folder in the dist directory based on actor data.
    Folder name format: imdb_id-name-YYYYMMDD_HHMMSS

    Args:
        actor_data (dict): Dictionary containing actor information
        script_dir (Path): Path to the script directory
    """

    # Get current timestamp in format YYYYMMDD_HHMMSS
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create folder name with timestamp
    folder_name = f"{actor_data['name']}"
    sub_folder_name = f"{actor_data['id']}-{timestamp}"

    # Create full path using script directory as base
    dist_dir = script_dir / "dist"
    project_folder = dist_dir / folder_name / sub_folder_name

    # Create directories
    project_folder.mkdir(parents=True, exist_ok=True)

    # Save actor data as JSON in the project folder
    actor_info_path = project_folder / "actor_info.json"
    with open(actor_info_path, "w", encoding="utf-8") as f:
        json.dump(actor_data, f, indent=2, ensure_ascii=False)

    return str(project_folder)


def download_video(url: str, output_path: str) -> str:
    """
    Download video from URL and save it locally

    Args:
        url (str): URL of the video to download
        output_path (str): Path where to save the video

    Returns:
        str: Path to the downloaded video file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Download the file with timeout and larger chunk size
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Get total file size
        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024 * 1024  # 1MB chunks for faster download
        downloaded = 0

        # Write the file with progress tracking
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # Calculate and display progress
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(
                            f"\rDownloading: {percent:.1f}% ({downloaded/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB)",
                            end="",
                        )
        print()  # New line after progress

        return output_path

    except requests.exceptions.Timeout:
        print("Error: Download timed out")
        raise
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        raise


def is_url(path: str) -> bool:
    """Check if the given path is a URL"""
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except:
        return False


def process_video(
    actor_data: dict,
    voice_id: str,
    video_path="",
    output_name="output.mp4",
    music_folder="default",
    music_volume=0.3,
    sfx_volume=0.45,
) -> None:
    """
    Process the video by setting up the project folder, generating TTS audio, and adding audio
    """
    try:
        # Get the directory where the script is located
        script_dir = Path(__file__).parent.absolute()

        # Validate actor data and files
        validate_actor_data(actor_data, script_dir)

        # Setup project folder
        project_path = setup_project_folder(actor_data, script_dir)
        print(f"Project folder created at: {project_path}")

        print("project_path", project_path)

        # Handle video path (URL or local file)
        if is_url(video_path):
            print(f"Downloading video from URL: {video_path}")
            video_filename = os.path.join(project_path, "source_video.mp4")
            video_path = download_video(video_path, video_filename)
            print(f"Video downloaded to: {video_path}")
        elif not os.path.exists(video_path):
            raise ValueError(f"Video file not found: {video_path}")

        # Construct paths
        music_directory = os.path.join(script_dir, "lib/audio", music_folder)

        print("folder_name", output_name)
        output_path = os.path.join(project_path, output_name)
        temp_audio_path = os.path.join(project_path, "temp-audio.m4a")

        # Call add_audio function
        add_audio(
            video_path=video_path,
            output_path=output_path,
            temp_audio_path=temp_audio_path,
            music_directory=music_directory,
            voice_id=voice_id,
            tts_data=actor_data["tts_data"],
            sfx_data=actor_data["sfx_data"],
            music_volume=music_volume,
            sfx_volume=sfx_volume,
        )

        print("Video processing completed successfully!", output_path)

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    # Check if type=short is provided in command line arguments
    if "type=short" in sys.argv:
        inp = input_shorts
    else:
        inp = input

    process_video(
        inp["actor_data"],
        inp["voice_id"],
        inp["video_path"],
        inp["output_name"],
        inp["music_folder"],
        music_volume=inp["music_volume"],
        sfx_volume=inp["sfx_volume"],
    )
