from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import List, Optional, Union, Literal, Dict, Any
from enum import Enum
import json
import os
from polly_constants import LanguageCode, VoiceId


class Metadata(BaseModel):
    projectId: Optional[str] = None
    title: Optional[str] = None
    tags: Optional[List[str]] = None


class VideoAsset(BaseModel):
    id: str
    source: str


class AudioAsset(BaseModel):
    id: str
    source: str


class Assets(BaseModel):
    video: VideoAsset
    audio: List[AudioAsset]


class BackgroundMusic(BaseModel):
    playlist: List[str]
    loop: bool = True
    volume: float = Field(default=0.3, ge=0.0, le=1.0)
    crossfadeDuration: float = Field(default=2.0, ge=0.0)


class ProviderConfig(BaseModel):
    voiceId: VoiceId = "Joanna"
    engine: Literal["standard", "neural", "long-form", "generative"] = "neural"
    textType: Literal["text", "ssml"] = "text"
    languageCode: Optional[LanguageCode] = None


class TTSData(BaseModel):
    text: str
    provider: Literal["aws-polly"] = "aws-polly"
    providerConfig: ProviderConfig = Field(default_factory=ProviderConfig)
    volume: float = Field(default=1.0, ge=0.0, le=1.0)
    duckingLevel: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    duckingFadeDuration: float = Field(default=0.0, ge=0.0)


class AudioData(BaseModel):
    assetId: str
    volume: float = Field(default=0.5, ge=0.0, le=1.0)
    duckingLevel: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    duckingFadeDuration: float = Field(default=0.0, ge=0.0)


class TTSEvent(BaseModel):
    start: float = Field(ge=0.0)
    type: Literal["tts"]
    data: TTSData


class AudioEvent(BaseModel):
    start: float = Field(ge=0.0)
    type: Literal["audio"]
    data: AudioData


TimelineEvent = Union[TTSEvent, AudioEvent]


class Encoding(BaseModel):
    preset: str = "medium"
    bitrate: Optional[str] = None
    audio_bitrate: Optional[str] = None
    fps: Optional[float] = None


class WebhookConfig(BaseModel):
    url: HttpUrl
    method: Literal["POST", "PUT"] = "POST"
    headers: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Union[str, int, float, bool]]] = None
    
    @field_validator('headers')
    @classmethod
    def validate_headers_size(cls, v):
        if v and len(json.dumps(v)) > int(os.getenv('WEBHOOK_MAX_HEADERS_SIZE', '1024')):
            raise ValueError("Headers exceed 1KB limit")
        return v
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata_size(cls, v):
        if v and len(json.dumps(v)) > int(os.getenv('WEBHOOK_MAX_METADATA_SIZE', '1024')):
            raise ValueError("Metadata exceed 1KB limit")
        return v


class NotificationsConfig(BaseModel):
    webhook: Optional[WebhookConfig] = None


class Output(BaseModel):
    destination: Optional[str] = None
    filename: str
    encoding: Optional[Encoding] = None


class JobSpec(BaseModel):
    metadata: Optional[Metadata] = None
    assets: Assets
    backgroundMusic: Optional[BackgroundMusic] = None
    timeline: List[TimelineEvent]
    output: Output
    notifications: Optional[NotificationsConfig] = None

    @field_validator("backgroundMusic")
    @classmethod
    def validate_playlist_assets(cls, v, info):
        if v and hasattr(info, "data") and "assets" in info.data:
            audio_ids = {audio.id for audio in info.data["assets"].audio}
            for playlist_id in v.playlist:
                if playlist_id not in audio_ids:
                    raise ValueError(
                        f"Playlist item '{playlist_id}' not found in assets.audio"
                    )
        return v

    @field_validator("timeline")
    @classmethod
    def validate_audio_assets(cls, v, info):
        if hasattr(info, "data") and "assets" in info.data:
            audio_ids = {audio.id for audio in info.data["assets"].audio}
            for event in v:
                if event.type == "audio" and event.data.assetId not in audio_ids:
                    raise ValueError(
                        f"Audio asset '{event.data.assetId}' not found in assets.audio"
                    )
        return v
