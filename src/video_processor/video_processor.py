import os
import logging
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, afx
from asset_manager import AssetManager
from tts_generator import TTSGenerator

logger = logging.getLogger(__name__)

# Default values
DEFAULTS = {
    "tts_volume": 1.0,
    "tts_ducking_level": 0.2,
    "audio_volume": 0.8,
    "audio_ducking_level": 0.5,
    "background_volume": 0.3,
    "ducking_fade_duration": 0.5,
    "temp_dir": "./tmp",  # Use local tmp directory in repo
}


class VideoProcessor:
    def __init__(self, temp_dir=None):
        self.asset_manager = AssetManager()
        self.tts_generator = TTSGenerator()
        self.temp_dir = temp_dir or DEFAULTS["temp_dir"]

        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)

    def process_video_job(self, job_spec):
        """Process a complete video job from job specification"""
        try:
            # Phase 1: Download audio assets first (fast fail)
            logger.info("Downloading audio assets...")
            audio_assets = self._download_audio_assets(job_spec["assets"]["audio"])

            # Phase 2: Download video asset
            logger.info("Downloading video asset...")
            video_path = self.asset_manager.download_asset(
                job_spec["assets"]["video"]["source"], self.temp_dir
            )

            # Phase 3: Load video and get duration
            video = VideoFileClip(video_path)
            video_duration = video.duration

            # Phase 4: Process timeline
            logger.info("Processing timeline...")
            background_music = None
            audio_clips = []

            for event in job_spec["timeline"]:
                if event["type"] == "backgroundMusic":
                    background_music = self._create_background_music(
                        event, audio_assets, video_duration
                    )
                elif event["type"] == "tts":
                    clip = self._create_tts_clip(event)
                    audio_clips.append(clip)
                elif event["type"] == "audio":
                    clip = self._create_audio_clip(event, audio_assets)
                    audio_clips.append(clip)

            # Phase 5: Combine audio layers
            logger.info("Combining audio layers...")
            all_audio = [background_music] if background_music else []
            all_audio.extend(audio_clips)
            final_audio = CompositeAudioClip(all_audio)

            # Phase 6: Final assembly and export
            logger.info("Creating final video...")
            final_video = video.with_audio(final_audio)

            output_filename = job_spec["output"].get("filename", "output.mp4")
            if not output_filename.lower().endswith(".mp4"):
                output_filename += ".mp4"
            local_output = os.path.join(self.temp_dir, output_filename)

            final_video.write_videofile(
                local_output,
                codec="libx264",
                audio_codec="aac",
                threads=6,
                preset="medium",
            )

            # Phase 7: Upload result
            logger.info("Uploading result...")
            result_url = self.asset_manager.upload_result(
                local_output, job_spec["output"]["destination"], output_filename
            )

            # Cleanup
            video.close()
            final_video.close()
            final_audio.close()
            for clip in audio_clips:
                clip.close()
            if background_music:
                background_music.close()

            return result_url

        except Exception as e:
            logger.error(f"Video processing failed: {str(e)}")
            raise

    def _download_audio_assets(self, audio_assets):
        """Download all audio assets and return lookup dict"""
        assets = {}
        for asset in audio_assets:
            local_path = self.asset_manager.download_asset(
                asset["source"], self.temp_dir
            )
            assets[asset["id"]] = local_path
        return assets

    def _create_background_music(self, event, audio_assets, video_duration):
        """Create background music from playlist"""
        details = event["details"]
        playlist = details["playlist"]
        volume = details.get("volume", DEFAULTS["background_volume"])

        # For now, use first track in playlist
        if playlist:
            asset_id = playlist[0]
            if asset_id in audio_assets:
                audio_clip = AudioFileClip(audio_assets[asset_id])

                # Loop if needed
                if details.get("loop", False) and audio_clip.duration < video_duration:
                    loops_needed = int(video_duration / audio_clip.duration) + 1
                    audio_clip = audio_clip.loop(loops_needed)

                # Trim to video duration
                if audio_clip.duration > video_duration:
                    audio_clip = audio_clip.subclipped(0, video_duration)

                return audio_clip.with_volume_scaled(volume)

        return None

    def _create_tts_clip(self, event):
        """Create TTS audio clip"""
        details = event["details"]
        start_time = event["start"]

        # Generate TTS
        tts_path = os.path.join(self.temp_dir, f"tts_{start_time}.mp3")
        self.tts_generator.generate_speech(
            details["text"], tts_path, details.get("voiceId", "Joanna")
        )

        # Create clip
        clip = AudioFileClip(tts_path)
        clip = clip.with_start(start_time)

        # Apply volume
        volume = details.get("volume", DEFAULTS["tts_volume"])
        clip = clip.with_volume_scaled(volume)

        return clip

    def _create_audio_clip(self, event, audio_assets):
        """Create audio clip from asset"""
        details = event["details"]
        start_time = event["start"]
        asset_id = details["assetId"]

        if asset_id not in audio_assets:
            raise ValueError(f"Audio asset {asset_id} not found")

        # Create clip
        clip = AudioFileClip(audio_assets[asset_id])
        clip = clip.with_start(start_time)

        # Apply volume
        volume = details.get("volume", DEFAULTS["audio_volume"])
        clip = clip.with_volume_scaled(volume)

        return clip
