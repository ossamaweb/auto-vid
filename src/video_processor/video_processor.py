import os
import logging
import time
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, afx
from asset_manager import AssetManager
from tts_generator import TTSGenerator
from webhook_notifier import WebhookNotifier


logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# Default temp directory (use Lambda's writable /tmp)
DEFAULT_TEMP_DIR = "/tmp"


class VideoProcessor:
    def __init__(self, temp_dir=None):
        self.asset_manager = AssetManager()
        self.tts_generator = TTSGenerator()
        self.webhook_notifier = WebhookNotifier()
        self.temp_dir = temp_dir or DEFAULT_TEMP_DIR

        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)

    def cleanup_job_dir(self, job_temp_dir):
        """Clean up job temporary directory"""

        try:
            import shutil

            if os.path.exists(job_temp_dir):
                shutil.rmtree(job_temp_dir)
                logger.info(f"Cleaned up job temp directory: {job_temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup job temp directory: {str(e)}")

    def process_video_job(self, job_id, job_spec):
        """Process a complete video job from job specification"""
        start_time = time.time()

        # Create unique job directory
        job_temp_dir = os.path.join(self.temp_dir, job_id)
        os.makedirs(job_temp_dir, exist_ok=True)

        try:
            return self._process_video_internal(
                job_id, job_spec, job_temp_dir, start_time
            )
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Video processing failed: {str(e)}")
            return {
                "success": False,
                "localOutputPath": None,
                "outputFilename": None,
                "duration": None,
                "fileSize": None,
                "processingTime": processing_time,
                "error": str(e),
                "tempDir": job_temp_dir,
            }

    def _process_video_internal(self, job_id, job_spec, job_temp_dir, start_time):
        try:
            # Phase 1: Download audio assets first (fast fail)
            logger.info("Downloading audio assets...")
            audio_assets = self._download_audio_assets(
                job_spec.assets.audio, job_temp_dir
            )

            # Phase 2: Download video asset
            logger.info("Downloading video asset...")
            downloaded_video_path = self.asset_manager.download_asset(
                job_spec.assets.video.source, job_temp_dir
            )

            # Rename input video to avoid conflict with output filename
            video_path = os.path.join(job_temp_dir, f"input_{job_id}.mp4")
            os.rename(downloaded_video_path, video_path)

            # Phase 3: Load video and get duration
            video = VideoFileClip(video_path)
            video_duration = video.duration

            # Phase 4: Process timeline and collect ducking ranges
            logger.info("Processing timeline...")
            background_music = None
            audio_clips = []
            ducking_ranges = []

            # Create background music from top-level backgroundMusic section
            if job_spec.backgroundMusic:
                background_music = self._create_background_music(
                    job_spec.backgroundMusic, audio_assets, video_duration
                )

            for index, event in enumerate(job_spec.timeline):
                if event.type == "tts":
                    clip = self._create_tts_clip(event, index, job_temp_dir)
                    audio_clips.append(clip)
                    # Collect ducking range if duckingLevel is specified
                    ducking_level = event.data.duckingLevel
                    fade_duration = event.data.duckingFadeDuration
                    if ducking_level is not None:
                        ducking_ranges.append(
                            {
                                "start": event.start,
                                "end": event.start + clip.duration,
                                "ducking_level": ducking_level,
                                "fade_duration": fade_duration,
                            }
                        )
                elif event.type == "audio":
                    clip = self._create_audio_clip(event, audio_assets)
                    audio_clips.append(clip)
                    # Collect ducking range if duckingLevel is specified
                    ducking_level = event.data.duckingLevel
                    fade_duration = event.data.duckingFadeDuration
                    if ducking_level is not None:
                        ducking_ranges.append(
                            {
                                "start": event.start,
                                "end": event.start + clip.duration,
                                "ducking_level": ducking_level,
                                "fade_duration": fade_duration,
                            }
                        )

            # Phase 5: Apply ducking to background music
            if background_music and ducking_ranges:
                logger.info("Applying ducking to background music...")
                background_music = self._apply_ducking(background_music, ducking_ranges)

            # Phase 6: Combine audio layers
            logger.info("Combining audio layers...")
            all_audio = [background_music] if background_music else []
            all_audio.extend(audio_clips)

            if not all_audio:
                # No audio clips at all - create silent audio matching video duration
                from moviepy import AudioClip

                final_audio = AudioClip(lambda t: [0, 0], duration=video_duration)
            else:
                final_audio = CompositeAudioClip(all_audio)

            # Trim clip if needed
            if video_duration < final_audio.duration:
                final_audio = final_audio.subclipped(0, video_duration)

            # Phase 7: Final assembly and export
            logger.info("Creating final video...")
            final_video = video.with_audio(final_audio)

            output_filename = job_spec.output.filename
            if not output_filename.lower().endswith(".mp4"):
                output_filename += ".mp4"

            local_output = os.path.join(job_temp_dir, output_filename)
            temp_audio_path = os.path.join(job_temp_dir, "temp_audio.m4a")

            # Get encoding parameters from job spec (Pydantic provides defaults)
            encoding = job_spec.output.encoding

            is_lambda = os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None

            final_video.write_videofile(
                local_output,
                codec="libx264",
                audio_codec="aac",
                preset=encoding.preset if encoding else "medium",
                bitrate=encoding.bitrate if encoding else None,
                audio_bitrate=encoding.audio_bitrate if encoding else None,
                fps=encoding.fps if encoding else None,
                temp_audiofile=temp_audio_path,
                remove_temp=True,
                threads=os.cpu_count() if is_lambda else 6,
                logger=None if is_lambda else "bar",
            )

            # Cleanup MoviePy objects before upload to free memory
            video.close()
            final_video.close()
            final_audio.close()
            for clip in audio_clips:
                clip.close()
            if background_music:
                background_music.close()

            # Return success result with local file path
            processing_time = time.time() - start_time
            file_size = os.path.getsize(local_output)

            return {
                "success": True,
                "localOutputPath": local_output,
                "outputFilename": output_filename,
                "duration": video_duration,
                "fileSize": file_size,
                "processingTime": processing_time,
                "error": None,
                "tempDir": job_temp_dir,
            }
        except Exception as e:
            raise e

    def _download_audio_assets(self, audio_assets, job_temp_dir):
        """Download all audio assets and return lookup dict"""
        assets = {}
        for asset in audio_assets:
            local_path = self.asset_manager.download_asset(asset.source, job_temp_dir)
            assets[asset.id] = local_path
        return assets

    def _create_background_music(self, bg_music_config, audio_assets, video_duration):
        """Create background music from playlist with crossfading"""
        playlist = bg_music_config.playlist
        volume = bg_music_config.volume
        background_music_loop = bg_music_config.loop
        crossfade_duration = bg_music_config.crossfadeDuration

        if not playlist:
            return None

        # Get audio files from playlist
        audio_files = []
        for asset_id in playlist:
            if asset_id in audio_assets:
                audio_files.append(audio_assets[asset_id])

        if not audio_files:
            return None

        background_tracks = []
        current_duration = 0
        track_index = 0

        while current_duration < video_duration:
            # Get next track from playlist (cycle through if loop enabled)
            if track_index >= len(audio_files):
                if background_music_loop:
                    track_index = 0
                else:
                    break

            audio_path = audio_files[track_index]
            audio_clip = AudioFileClip(audio_path)
            audio_clip = audio_clip.with_volume_scaled(volume)

            # Calculate clip duration needed
            remaining_duration = video_duration - current_duration
            if audio_clip.duration is None:
                continue

            clip_duration = min(
                audio_clip.duration, remaining_duration + crossfade_duration
            )

            # Trim clip if needed
            if clip_duration < audio_clip.duration:
                audio_clip = audio_clip.subclipped(0, clip_duration)

            # Add crossfade effects
            if len(background_tracks) > 0:  # Not first track
                audio_clip = audio_clip.with_effects(
                    [afx.AudioFadeIn(crossfade_duration)]
                )
                audio_clip = audio_clip.with_start(
                    current_duration - crossfade_duration
                )
            else:
                audio_clip = audio_clip.with_start(current_duration)

            if current_duration + clip_duration < video_duration:  # Not last track
                audio_clip = audio_clip.with_effects(
                    [afx.AudioFadeOut(crossfade_duration)]
                )

            background_tracks.append(audio_clip)
            current_duration += clip_duration - (
                crossfade_duration if len(background_tracks) > 1 else 0
            )
            track_index += 1

            # Break if close enough to target duration
            if video_duration - current_duration < 1:
                break

        if not background_tracks:
            return None

        # Create composite and trim to exact duration
        final_audio = CompositeAudioClip(background_tracks)
        if final_audio.duration > video_duration:
            final_audio = final_audio.subclipped(0, video_duration)

        return final_audio

    def _create_tts_clip(self, event, index, job_temp_dir):
        """Create TTS audio clip"""
        data = event.data
        start_time = event.start

        # Get provider config (Pydantic provides defaults)
        provider = data.provider
        provider_config = data.providerConfig

        # Extract AWS Polly config
        voice_id = provider_config.voiceId
        engine = provider_config.engine
        language_code = provider_config.languageCode
        text_type = provider_config.textType

        # Generate TTS with unique filename using timeline index
        tts_path = os.path.join(job_temp_dir, f"tts_{index}_{start_time}.mp3")
        self.tts_generator.generate_speech(
            data.text, tts_path, voice_id, engine, language_code, text_type
        )

        # Create clip
        clip = AudioFileClip(tts_path)
        clip = clip.with_start(start_time)

        # Apply volume
        volume = data.volume
        clip = clip.with_volume_scaled(volume)

        return clip

    def _create_audio_clip(self, event, audio_assets):
        """Create audio clip from asset"""
        data = event.data
        start_time = event.start
        asset_id = data.assetId

        if asset_id not in audio_assets:
            raise ValueError(f"Audio asset {asset_id} not found")

        # Create clip
        clip = AudioFileClip(audio_assets[asset_id])
        clip = clip.with_start(start_time)

        # Apply volume
        volume = data.volume
        clip = clip.with_volume_scaled(volume)

        return clip

    def _apply_ducking(self, background_music, ducking_ranges):
        """Apply ducking to background music based on ranges"""
        # Sort ranges by start time
        ducking_ranges.sort(key=lambda x: x["start"])

        # Merge overlapping ranges
        merged_ranges = []
        if ducking_ranges:
            current_range = ducking_ranges[0]
            for next_range in ducking_ranges[1:]:
                if next_range["start"] <= current_range["end"]:
                    # Ranges overlap, merge them
                    current_range["end"] = max(current_range["end"], next_range["end"])
                    # Use more aggressive ducking level (lower value)
                    current_range["ducking_level"] = min(
                        current_range["ducking_level"], next_range["ducking_level"]
                    )
                    # Use longer fade duration
                    current_range["fade_duration"] = max(
                        current_range["fade_duration"], next_range["fade_duration"]
                    )
                else:
                    # No overlap, add current range and start new one
                    merged_ranges.append(current_range)
                    current_range = next_range
            merged_ranges.append(current_range)

        # Apply ducking for each merged range
        for range_info in merged_ranges:
            if range_info["fade_duration"] > 0:
                # Apply fade effects when fade duration is specified
                background_music = background_music.with_effects(
                    [
                        afx.AudioFadeIn(range_info["fade_duration"]),
                        afx.AudioFadeOut(range_info["fade_duration"]),
                    ]
                ).with_volume_scaled(
                    range_info["ducking_level"], range_info["start"], range_info["end"]
                )
            else:
                # Apply instant volume change when fade duration is 0
                background_music = background_music.with_volume_scaled(
                    range_info["ducking_level"], range_info["start"], range_info["end"]
                )

        return background_music
