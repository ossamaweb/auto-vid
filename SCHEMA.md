## Video Job Specification: JSON Schema Documentation

This document outlines the schema for the "Video Job Specification" JSON file. This declarative structure serves as the "contract" for the video processing engine, describing all the assets, timeline events, and output settings required to generate a complete video.

### Top-Level Structure

The JSON object has six main keys:

- `metadata`: Information _about_ the project for tracking and organization.
- `assets`: A library of all media files (video, audio) to be used.
- `backgroundMusic`: Configuration for continuous background audio throughout the video.
- `timeline`: A chronological sequence of timed events that happen _on_ the video.
- `output`: Specifications for the final rendered file.
- `notifications`: Configuration for job completion notifications.

---

### Section Breakdown

#### 1. `jobInfo` (Object, Optional)

Contains general information about the video job.

- `"projectId"` (String, Optional, Max 100 chars): A unique identifier for the job or project.
- `"title"` (String, Optional, Max 200 chars): The human-readable title of the video.
- `"tags"` (Array of Strings, Optional, Max 10 tags, 50 chars each): A list of tags for searching and categorization.

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

- `"playlist"` (Array of Strings, Required): An ordered list of audio asset IDs from the `assets` section to be played in sequence.
- `"loop"` (Boolean, Default: true): If `true`, the entire playlist will repeat if the video is longer than the playlist's combined duration.
- `"volume"` (Float, 0.0-1.0, Default: 0.3): The base volume for the background music.
- `"crossfadeDuration"` (Float, Default: 2.0, ≥0.0): The time in seconds to crossfade between tracks in the playlist.

#### 4. `timeline` (Array of Objects, Required, Non-empty)

Defines all the timed creative events that occur during the video. The engine processes this array in chronological order. Each object is an "event" with a `type` and `start` time. Timeline cannot be empty.

##### Event Type: `tts` (Text-to-Speech)

Defines a voiceover event.

- `"start"` (Float, ≥0.0): The time in seconds when the voiceover should begin.
- `"type": "tts"`
- `"data"` (Object):
  - `"text"` (String, Required): The text to be converted to speech.
  - `"provider"` (Literal["aws-polly"], Default: "aws-polly"): TTS provider to use.
  - `"providerConfig"` (Object, Optional): Provider-specific configuration. See [AWS Polly SynthesizeSpeech API](https://docs.aws.amazon.com/polly/latest/dg/API_SynthesizeSpeech.html) for complete reference.
    - `"voiceId"` (String, Default: "Joanna"): Voice ID for the TTS provider. Must be one of AWS Polly's supported voices.
    - `"engine"` (String, Default: "neural"): TTS engine type. Options: "standard", "neural", "long-form", "generative".
    - `"languageCode"` (String, Optional): Language code for the voice (e.g., "en-US", "es-ES"). If not specified, uses the voice's default language.
    - `"textType"` (String, Default: "text"): Text format type. Options: "text" or "ssml" for Speech Synthesis Markup Language support.
  - `"volume"` (Float, 0.0-1.0, Default: 1.0): The volume of this specific TTS clip.
  - `"duckingLevel"` (Float, 0.0-1.0, Optional): If specified, background music will duck to this volume level during this clip.
  - `"duckingFadeDuration"` (Float, ≥0.0, Default: 0.0): Time in seconds for the ducking fade transition.

##### Event Type: `audio`

Defines a sound effect or other pre-recorded audio clip event.

- `"start"` (Float, ≥0.0): The time in seconds when the audio should begin.
- `"type": "audio"`
- `"data"` (Object):
  - `"assetId"` (String, Required): The ID of the audio asset to play from the `assets` section.
  - `"volume"` (Float, 0.0-1.0, Default: 0.5): The volume of this specific audio clip.
  - `"duckingLevel"` (Float, 0.0-1.0, Optional): If specified, background music will duck to this volume level during this clip.
  - `"duckingFadeDuration"` (Float, ≥0.0, Default: 0.0): Time in seconds for the ducking fade transition.

#### 5. `output` (Object, Required)

Defines the properties of the final, rendered video file.

- `"destination"` (String, Optional): The URI of the destination folder (e.g., `s3://my-bucket/outputs/`). If not specified, uses the managed S3 bucket created by the CloudFormation stack.
- `"filename"` (String, Required): The name of the final output file (e.g., `"final-video.mp4"`).
- `"encoding"` (Object, Optional): MP4 video encoding parameters (uses defaults if not specified).
  - `"preset"` (String, Default: "medium"): FFmpeg preset for encoding speed vs quality tradeoff.
  - `"bitrate"` (String, Optional): Video bitrate (e.g., "2500k", "5M").
  - `"audio_bitrate"` (String, Optional): Audio bitrate (e.g., "128k", "320k").
  - `"fps"` (Float, Optional): Output frame rate.

#### 6. `notifications` (Object, Optional)

Defines notification settings for job completion.

- `"webhook"` (Object, Optional): Webhook notification configuration.
  - `"url"` (String, Required): The webhook endpoint URL (must be HTTPS for production).
  - `"method"` (String, Default: "POST"): HTTP method to use. Options: "POST" or "PUT".
  - `"headers"` (Object, Optional): Custom HTTP headers to send with the webhook request. Maximum size: 1KB.
  - `"metadata"` (Object, Optional): Custom metadata to include in the webhook payload. Supports string, number, and boolean values. Maximum size: 1KB.

**Webhook Payload:**
The webhook will receive a JSON payload with the following structure:
```json
{
  "jobId": "uuid",
  "status": "completed|failed",
  "submittedAt": "2024-01-01T12:00:00Z",
  "updatedAt": "2024-01-01T12:01:00Z",
  "completedAt": "2024-01-01T12:05:00Z",
  "processingTime": 120.5,
  "output": {
    "url": "https://bucket.s3.amazonaws.com/outputs/video.mp4?X-Amz-Algorithm=...",
    "urlExpiresAt": "2024-01-02T12:00:00Z",
    "s3Uri": "s3://bucket/outputs/video.mp4",
    "duration": 45.2,
    "size": 15728640
  },
  "error": null,
  "metadata": {...}
}
```

**Payload Fields:**
- `jobId` - Unique job identifier
- `status` - "completed" or "failed"
- `submittedAt` - ISO 8601 submission time (UTC)
- `updatedAt` - ISO 8601 last update time (UTC)
- `completedAt` - ISO 8601 completion time (UTC)
- `processingTime` - Duration in seconds (rounded to 2 decimals)
- `output.url` - Pre-signed download URL (null if generation failed)
- `output.urlExpiresAt` - ISO 8601 expiration time for download URL (null if no URL)
- `output.s3Uri` - Internal S3 URI reference (null for local files)
- `output.duration` - Video length in seconds (null on failure)
- `output.size` - File size in bytes (null on failure)
- `error` - Error message (failure only)
- `metadata` - Custom user-provided metadata

**Note:** The `output` section is always present with all fields included. On failure or when unavailable, fields are set to `null`.

**URL Behavior:**
- `url` - Pre-signed download URL (expires in 24 hours by default)
- `urlExpiresAt` - Only present when `url` is a valid pre-signed URL
- `s3Uri` - Always present for S3 uploads, `null` for local files
- If pre-signed URL generation fails, `url` and `urlExpiresAt` will be `null`
```

**Retry Logic:**
- 3 automatic retry attempts with exponential backoff (1s, 2s, 4s)
- 4xx errors are not retried (client configuration issues)
- 5xx errors and network timeouts are retried
- 30-second request timeout

### S3 Bucket Usage

The system supports both managed and custom S3 buckets:

**Managed Bucket (Recommended for beginners):**
- Automatically created during deployment
- Bucket name: `auto-vid-s3-bucket-{stack-name}-{account-id}`
- Available to Lambda functions via `AUTO_VID_BUCKET` environment variable
- Used when `destination` is omitted from output configuration
- Organized with `/assets/` and `/outputs/` prefixes
- Example bucket name: `auto-vid-s3-bucket-mystack-123456789012`

**Custom Bucket (Advanced users):**
- Specify full S3 URI in asset sources and output destination
- Requires proper IAM permissions for the Lambda functions
- Example: `s3://my-custom-bucket/my-folder/`

---

### Complete Example: `job_spec.json`

```json
{
  "$schema": "https://your-domain.com/schemas/video-job-v2.json",
  "jobInfo": {
    "projectId": "simple_example",
    "title": "Background Music Only Example"
  },
  "assets": {
    "video": {
      "id": "main_video",
      "source": "s3://auto-vid-s3-bucket-mystack-123456789012/assets/input.mp4"
    },
    "audio": [
      {
        "id": "bgm_track",
        "source": "s3://auto-vid-s3-bucket-mystack-123456789012/assets/background.mp3"
      }
    ]
  },
  "backgroundMusic": {
    "playlist": ["bgm_track"],
    "volume": 0.4
  },
  "timeline": [],
  "output": {
    "filename": "video-with-music.mp4"
  },
  "notifications": {
    "webhook": {
      "url": "https://your-app.com/webhook/video-complete",
      "headers": {
        "Authorization": "Bearer your-token"
      },
      "metadata": {
        "projectType": "background-music-only",
        "priority": "normal"
      }
    }
  }
}
```

### Complete Example with Custom S3 Bucket: `job_spec.json`

```json
{
  "$schema": "https://your-domain.com/schemas/video-job-v2.json",
  "jobInfo": {
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
          "engine": "neural",
          "languageCode": "en-US",
          "textType": "text"
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
          "engine": "neural",
          "languageCode": "en-US",
          "textType": "text"
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
    "filename": "tyler-perry-final-v2.mp4",
    "encoding": {
      "preset": "fast",
      "bitrate": "2500k"
    }
  },
  "notifications": {
    "webhook": {
      "url": "https://api.example.com/webhooks/video-complete",
      "headers": {
        "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "X-Project-ID": "tyler-perry-series"
      },
      "metadata": {
        "series": "celebrity-earnings",
        "episode": 1,
        "duration_target": 90,
        "auto_publish": true
      }
    }
  }
}
```
