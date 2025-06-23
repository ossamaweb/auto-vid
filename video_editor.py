import os
import random
from moviepy import (
    afx,
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_audioclips,
)
from tts_generator import TTSGenerator


def get_audio_files(music_directory):
    """
    Get all audio files from the specified directory
    Returns a list of audio file paths
    """
    audio_files = []
    for file in os.listdir(music_directory):
        if file.endswith((".mp3", ".wav", ".m4a")):
            audio_files.append(os.path.join(music_directory, file))
    return audio_files


def generate_tts_audio(
    tts: TTSGenerator, text: str, output_path: str, voice_id="Joanna"
) -> str:
    """
    Generate TTS audio from text and save it to the specified path

    Args:
        tts (TTSGenerator): Instance of TTSGenerator to use
        text (str): Text to convert to speech
        output_path (str): Path where to save the audio file

    Returns:
        str: Path to the generated audio file
    """
    try:
        return tts.generate_speech(
            text=text,
            output_path=output_path,
            voice_id=voice_id,  # Using Matthew voice for a professional sound
            engine="generative",
        )
    except Exception as e:
        print(f"Error generating TTS audio: {str(e)}")
        raise


def create_background_music(
    audio_files,
    output_path: str,
    total_duration,
    volume=1.0,
):
    """
    Create a continuous background music track from random audio files
    Returns an AudioClip that matches the video duration

    Args:
        audio_files: List of audio file paths
        output_path (str): Path to the output video file
        total_duration: Total duration of the background music
        volume: Volume level for the background music
    """
    background_tracks = []
    current_duration = 0
    crossfade_duration = 2.0  # 2 second crossfade

    # Create a shuffled sequence of all tracks
    track_sequence = []

    while current_duration < total_duration:
        # Randomly select an audio file
        if not track_sequence:  # If we've used all tracks
            track_sequence = random.sample(audio_files, len(audio_files))

        audio_path = track_sequence.pop()  # Get next track from sequence

        audio_clip = AudioFileClip(audio_path)

        # Apply volume adjustment
        audio_clip = audio_clip.with_volume_scaled(volume)

        # Calculate how much of this clip we need
        remaining_duration = total_duration - current_duration
        clip_duration = min(
            audio_clip.duration, remaining_duration + crossfade_duration
        )

        # Take only the portion we need
        if clip_duration < audio_clip.duration:
            audio_clip = audio_clip.subclipped(0, clip_duration)

        # Add fades for crossfading
        if len(background_tracks) > 0:  # Not the first track
            audio_clip = audio_clip.with_effects([afx.AudioFadeIn(crossfade_duration)])
            # Start this clip earlier by crossfade_duration
            audio_clip = audio_clip.with_start(current_duration - crossfade_duration)

        if current_duration + clip_duration < total_duration:  # Not the last track
            audio_clip = audio_clip.with_effects([afx.AudioFadeOut(crossfade_duration)])

        background_tracks.append(audio_clip)
        current_duration += (
            clip_duration - crossfade_duration
        )  # Subtract crossfade duration since clips overlap

        # If we're close enough to the target duration, break
        if total_duration - current_duration < 1:
            break

    # Create composite of all audio clips (they will overlap properly due to their start times)
    final_audio = CompositeAudioClip(background_tracks)

    # Trim to exact duration needed
    if final_audio.duration > total_duration:
        final_audio = final_audio.subclipped(0, total_duration)

    # Save background track filenames to a text file
    try:
        output_dir = os.path.dirname(output_path)
        tracks_file = os.path.join(output_dir, "background_tracks.txt")
        track_filenames = [track.filename for track in background_tracks]
        with open(tracks_file, "w") as f:
            f.write("\n".join(track_filenames))
    except Exception as e:
        print(f"Warning: Failed to save background tracks file: {str(e)}")

    return final_audio


def add_audio(
    video_path,
    music_directory,
    output_path,
    temp_audio_path,
    voice_id,
    tts_data,  # List of dictionaries with time and data (tts text) fields
    sfx_data,  # List of dictionaries with time and data (filename) fields
    tts_ducking_level=0.2,
    tts_fade_duration=1.0,
    sfx_volume=0.45,
    sfx_ducking_level=0.5,
    sfx_fade_duration=0.2,
    music_volume=0.3,
):
    """
    Add background music and TTS to a video file
    Parameters:
    - video_path: Path to the input video file
    - music_directory: Directory containing music files
    - output_path: Path for the output video
    - temp_audio_path: Path for temporary audio file
    - tts_data: List of dictionaries containing TTS timing and text data
    - sfx_data: List of dictionaries containing SFX timing and file data
    - music_volume: Volume level for background music (0.0 to 1.0)
    - sfx_volume: Volume level for sound effects (0.0 to 1.0)
    - end_screen_duration: The duration of youtube end screen
    """
    # Initialize variables to None for cleanup
    video = None
    background_music = None
    final_audio = None
    final_video = None
    sfx_clips = []
    tts_clips = []

    try:
        # Load the video
        print("Loading video...")
        video = VideoFileClip(video_path)

        # Initialize TTS Generator once
        tts = TTSGenerator()

        # Create a temporary directory for TTS files
        temp_tts_dir = os.path.join(os.path.dirname(temp_audio_path), "tts_temp")
        os.makedirs(temp_tts_dir, exist_ok=True)

        # Generate TTS audio and collect ranges
        all_ranges = []
        for tts_item in tts_data:
            # Generate unique filename for each TTS
            tts_file = os.path.join(temp_tts_dir, f"{tts_item['id']}.mp3")
            print(f"Generating TTS audio for {tts_item['id']}...")

            # Generate the TTS audio
            generate_tts_audio(tts, tts_item["data"], tts_file, voice_id)

            # Load the generated audio clip
            tts_clip = AudioFileClip(tts_file)

            # Calculate start time based on start/end fields
            start_time = None
            if tts_item.get("end") not in [None, "null"]:
                # If end is specified, calculate start time
                end_time = tts_item["end"]
                if end_time < 0:
                    # Negative end time means X seconds before video end
                    end_time = round(video.duration + end_time, 2)
                start_time = end_time - tts_clip.duration
            elif tts_item.get("start") not in [None, "null"]:
                # If start is specified, use it directly
                start_time = tts_item["start"]
                if start_time < 0:
                    # Negative start time means X seconds before video end
                    start_time = round(video.duration + start_time, 2)

            # Position the clip
            tts_clip = tts_clip.with_start(start_time)
            tts_clips.append(tts_clip)

            # Add TTS range directly to all_ranges
            all_ranges.append(
                {
                    "start": start_time,
                    "end": round(start_time + tts_clip.duration, 2),
                    "ducking_level": tts_ducking_level,
                    "fade_duration": tts_fade_duration,
                }
            )

        # Handle SFX ranges
        print("Loading SFX clips...")
        for sfx in sfx_data:
            sfx_path = os.path.join("lib", "sfx", sfx["data"])
            sfx_clip = AudioFileClip(sfx_path)
            sfx_clip = sfx_clip.with_start(sfx["start"])
            sfx_clip = sfx_clip.with_volume_scaled(sfx_volume)
            sfx_clips.append(sfx_clip)

            # Add SFX range directly to all_ranges
            all_ranges.append(
                {
                    "start": sfx["start"],
                    "end": round(sfx["start"] + sfx_clip.duration, 2),
                    "ducking_level": sfx_ducking_level,
                    "fade_duration": sfx_fade_duration,
                }
            )

        # Sort all ranges by start time
        all_ranges.sort(key=lambda x: x["start"])

        print("all_ranges", all_ranges)

        # Merge overlapping ranges
        final_merged_ranges = []
        if all_ranges:
            current_range = all_ranges[0]
            for next_range in all_ranges[1:]:
                if next_range["start"] <= current_range["end"]:
                    # Ranges overlap, merge them
                    current_range["end"] = max(current_range["end"], next_range["end"])
                    # Use the more aggressive ducking level (lower value) and longer fade duration
                    current_range["ducking_level"] = min(
                        current_range["ducking_level"], next_range["ducking_level"]
                    )
                    current_range["fade_duration"] = max(
                        current_range["fade_duration"], next_range["fade_duration"]
                    )
                else:
                    # No overlap, add current range and start new one
                    final_merged_ranges.append(current_range)
                    current_range = next_range
            final_merged_ranges.append(current_range)

        # Get available audio files and create background music
        print("Creating background music...")
        audio_files = get_audio_files(music_directory)
        if not audio_files:
            raise Exception("No audio files found in the specified directory")

        # Create background music with volume adjustment
        background_music = create_background_music(
            audio_files, output_path, video.duration, volume=music_volume
        )

        # Apply final volume changes for all ranges
        for range in final_merged_ranges:
            background_music = background_music.with_effects(
                [
                    afx.AudioFadeIn(range["fade_duration"]),
                    afx.AudioFadeOut(range["fade_duration"]),
                ]
            ).with_volume_scaled(range["ducking_level"], range["start"], range["end"])

        # Combine all audio tracks
        print("Combining audio tracks...")
        final_audio = CompositeAudioClip([background_music, *tts_clips, *sfx_clips])

        # Combine video with final audio
        print("Combining video with audio...")
        final_video = video.with_audio(final_audio)

        # Write the final video
        print("Writing final video...")
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=temp_audio_path,
            remove_temp=True,
            threads=6,
            preset="medium",
            # logger=None,
        )

        print("Video processing completed successfully!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise
    finally:
        # Clean up all clips and temporary files
        for clip in [
            video,
            background_music,
            final_audio,
            final_video,
            *sfx_clips,
            *tts_clips,
        ]:
            try:
                if clip is not None:
                    clip.close()
            except:
                pass

        # Clean up temporary TTS directory
        # try:
        #     import shutil

        #     shutil.rmtree(temp_tts_dir)
        # except:
        #     pass
