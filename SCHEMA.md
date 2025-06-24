## Video Job Specification: JSON Schema Documentation

This document outlines the schema for the "Video Job Specification" JSON file. This declarative structure serves as the "contract" for the video processing engine, describing all the assets, timeline events, and output settings required to generate a complete video.

### Top-Level Structure

The JSON object has five main keys:

- `metadata`: Information _about_ the project for tracking and organization.
- `assets`: A library of all media files (video, audio) to be used.
- `backgroundMusic`: Configuration for continuous background audio throughout the video.
- `timeline`: A chronological sequence of timed events that happen _on_ the video.
- `output`: Specifications for the final rendered file.

---

### Section Breakdown

#### 1. `metadata` (Object, Optional)

Contains general information about the video job.

- `"projectId"` (String, Optional): A unique identifier for the job or project.
- `"title"` (String, Recommended): The human-readable title of the video.
- `"tags"` (Array of Strings, Optional): A list of tags for searching and categorization.

#### 2. `assets` (Object, Required)

A manifest of all source media. The `id` of each asset is used to reference it later in the timeline.

- `"video"` (Object, Required): The primary background video clip.
  - `"id"` (String): A unique ID for this video asset (e.g., `"main_video"`).
  - `"source"` (String): The URI of the video file (e.g., `s3://my-bucket/inputs/video.mp4`).
- `"audio"` (Array of Objects, Required): A list of all audio files (music, SFX).
  - `"id"` (String): A unique ID for this audio asset (e.g., `"bgm_main"`, `"sfx_cheer"`).
  - `"source"` (String): The URI of the audio file.

#### 3. `backgroundMusic` (Object, Optional)

Defines the continuous background audio track that plays throughout the entire video.

- `"playlist"` (Array of Strings): An ordered list of audio asset IDs from the `assets` section to be played in sequence.
- `"loop"` (Boolean): If `true`, the entire playlist will repeat if the video is longer than the playlist's combined duration.
- `"volume"` (Float, 0.0-1.0): The base volume for the background music.
- `"crossfadeDuration"` (Float, Optional): The time in seconds to crossfade between tracks in the playlist.

#### 4. `timeline` (Array of Objects, Required)

Defines all the timed creative events that occur during the video. The engine processes this array in chronological order. Each object is an "event" with a `type` and `start` time.

##### Event Type: `tts` (Text-to-Speech)

Defines a voiceover event.

- `"start"` (Float): The time in seconds when the voiceover should begin.
- `"type": "tts"`
- `"data"` (Object):
  - `"text"` (String): The text to be converted to speech.
  - `"provider"` (String, Optional): TTS provider to use (default: "aws-polly").
  - `"providerConfig"` (Object): Provider-specific configuration.
    - For AWS Polly: `{"voiceId": "Matthew", "engine": "generative"}`
  - `"volume"` (Float, 0.0-1.0, Optional): The volume of this specific TTS clip.
  - `"duckingLevel"` (Float, 0.0-1.0, Optional): If specified, background music will duck to this volume level during this clip.
  - `"duckingFadeDuration"` (Float, Optional): Time in seconds for the ducking fade transition (only used if duckingLevel is specified).

##### Event Type: `audio`

Defines a sound effect or other pre-recorded audio clip event.

- `"start"` (Float): The time in seconds when the audio should begin.
- `"type": "audio"`
- `"data"` (Object):
  - `"assetId"` (String): The ID of the audio asset to play from the `assets` section.
  - `"volume"` (Float, 0.0-1.0, Optional): The volume of this specific audio clip.
  - `"duckingLevel"` (Float, 0.0-1.0, Optional): If specified, background music will duck to this volume level during this clip.
  - `"duckingFadeDuration"` (Float, Optional): Time in seconds for the ducking fade transition (only used if duckingLevel is specified).

#### 5. `output` (Object, Required)

Defines the properties of the final, rendered video file.

- `"destination"` (String): The URI of the destination folder (e.g., `s3://my-bucket/outputs/`).
- `"filename"` (String): The name of the final output file (e.g., `"final-video.mp4"`).
- `"encoding"` (Object, Optional): MP4 video encoding parameters (uses MoviePy defaults if not specified).
  - `"preset"` (String, Optional): FFmpeg preset - "ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo" (default: "medium").
  - `"bitrate"` (String, Optional): Video bitrate (e.g., "2500k", "5M").
  - `"audio_bitrate"` (String, Optional): Audio bitrate (e.g., "128k", "320k").
  - `"fps"` (Number, Optional): Output frame rate.

---

### Complete Example: `job_spec.json`

```json
{
  "$schema": "https://your-domain.com/schemas/video-job-v2.json",
  "metadata": {
    "projectId": "project_name",
    "title": "My Automated Video v1",
    "tags": ["automated"]
  },
  "assets": {
    "video": {
      "id": "main_video",
      "source": "s3://my-hackathon-bucket-inputs/input.mp4"
    },
    "audio": [
      {
        "id": "bgm_cinematic",
        "source": "s3://my-hackathon-bucket-assets/music/cinematic-happy.mp3"
      },
      {
        "id": "sfx_swoosh",
        "source": "s3://my-hackathon-bucket-assets/sfx/swoosh.wav"
      },
      {
        "id": "sfx_cheer",
        "source": "s3://my-hackathon-bucket-assets/sfx/cheers.wav"
      }
    ]
  },
  "backgroundMusic": {
    "playlist": ["bgm_cinematic"],
    "loop": true,
    "volume": 0.3,
    "crossfadeDuration": 2.0
  },
  "timeline": [
    {
      "start": 0,
      "type": "tts",
      "data": {
        "text": "What if I told you Tyler Perry isn't just a filmmaker, but a financial titan whose career earnings will absolutely shock you?",
        "provider": "aws-polly",
        "providerConfig": {
          "voiceId": "Matthew",
          "engine": "generative"
        },
        "duckingLevel": 0.1,
        "duckingFadeDuration": 1.0
      }
    },
    {
      "start": 48.5,
      "type": "audio",
      "data": {
        "assetId": "sfx_swoosh",
        "volume": 0.8
      }
    },
    {
      "start": 49,
      "type": "tts",
      "data": {
        "text": "Tyler Perry made a bold move on Diary of a Mad Black Woman, funding half the $5.5 million budget himself!",
        "provider": "aws-polly",
        "providerConfig": {
          "voiceId": "Matthew",
          "engine": "generative"
        },
        "duckingLevel": 0.1,
        "duckingFadeDuration": 1.0
      }
    },
    {
      "start": 73,
      "type": "audio",
      "data": {
        "assetId": "sfx_cheer",
        "volume": 0.9,
        "duckingLevel": 0.4,
        "duckingFadeDuration": 0.5
      }
    }
  ],
  "output": {
    "destination": "s3://my-hackathon-bucket-outputs/",
    "filename": "tyler-perry-final-v2.mp4",
    "encoding": {
      "preset": "fast",
      "bitrate": "2500k"
    }
  }
}
```
