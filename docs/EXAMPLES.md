# Advanced Examples

## Social Media Video with Sound Effects

```json
{
  "jobInfo": {
    "projectId": "social_media_campaign",
    "title": "Product Launch Video",
    "tags": ["social media", "product launch", "tts"]
  },
  "assets": {
    "video": {
      "id": "main_video",
      "source": "s3://your-bucket/product-demo.mp4"
    },
    "audio": [
      {
        "id": "background_music",
        "source": "s3://your-bucket/upbeat-music.mp3"
      },
      {
        "id": "whoosh_sfx",
        "source": "s3://your-bucket/whoosh.wav"
      },
      {
        "id": "impact_sfx",
        "source": "s3://your-bucket/impact.wav"
      }
    ]
  },
  "backgroundMusic": {
    "playlist": ["background_music"],
    "volume": 0.25,
    "crossfadeDuration": 1.5
  },
  "timeline": [
    {
      "start": 2.0,
      "type": "tts",
      "data": {
        "text": "Introducing our revolutionary new product!",
        "providerConfig": {
          "voiceId": "Matthew",
          "engine": "neural"
        },
        "volume": 0.9,
        "duckingLevel": 0.3
      }
    },
    {
      "start": 5.5,
      "type": "audio",
      "data": {
        "assetId": "whoosh_sfx",
        "volume": 0.7
      }
    },
    {
      "start": 8.0,
      "type": "tts",
      "data": {
        "text": "Available now with a 30% discount!",
        "providerConfig": {
          "voiceId": "Matthew",
          "engine": "neural"
        },
        "volume": 0.9,
        "duckingLevel": 0.3
      }
    },
    {
      "start": 12.0,
      "type": "audio",
      "data": {
        "assetId": "impact_sfx",
        "volume": 0.8
      }
    }
  ],
  "output": {
    "filename": "product-launch-final.mp4",
    "encoding": {
      "preset": "medium"
    }
  },
  "notifications": {
    "webhook": {
      "url": "https://your-app.com/webhook/video-complete",
      "method": "POST",
      "headers": {
        "Authorization": "Bearer your-api-token",
        "X-Campaign-ID": "launch-2024"
      },
      "metadata": {
        "campaign": "product_launch",
        "priority": "high",
        "team": "marketing"
      }
    }
  }
}
```

## API Examples

### TTS-only Video

```bash
curl -X POST $API_URL/submit -H "Content-Type: application/json" -d '{
  "jobInfo": {"projectId": "tts_demo", "title": "Voice Only"},
  "assets": {
    "video": {"id": "main", "source": "s3://bucket/video.mp4"},
    "audio": []
  },
  "timeline": [{
    "start": 3.0,
    "type": "tts",
    "data": {
      "text": "This is a text-to-speech demonstration.",
      "providerConfig": {"voiceId": "Joanna", "engine": "neural"}
    }
  }],
  "output": {"filename": "tts-demo.mp4"}
}'
```

### Background Music Only

```bash
curl -X POST $API_URL/submit -H "Content-Type: application/json" -d '{
  "jobInfo": {"projectId": "music_demo", "title": "Music Only"},
  "assets": {
    "video": {"id": "main", "source": "s3://bucket/video.mp4"},
    "audio": [{"id": "bgm", "source": "s3://bucket/music.mp3"}]
  },
  "backgroundMusic": {"playlist": ["bgm"], "volume": 0.4},
  "timeline": [],
  "output": {"filename": "music-demo.mp4"}
}'
```

### Multi-language with SSML

```bash
curl -X POST $API_URL/submit -H "Content-Type: application/json" -d '{
  "jobInfo": {"projectId": "multilang", "title": "Spanish Demo"},
  "assets": {
    "video": {"id": "main", "source": "s3://bucket/video.mp4"},
    "audio": []
  },
  "timeline": [{
    "start": 2.0,
    "type": "tts",
    "data": {
      "text": "<speak>¡Hola! <break time=\"1s\"/> Bienvenidos a Auto-Vid.</speak>",
      "providerConfig": {
        "voiceId": "Lupe",
        "engine": "neural",
        "textType": "ssml",
        "languageCode": "es-US"
      }
    }
  }],
  "output": {"filename": "spanish-demo.mp4"}
}'
```