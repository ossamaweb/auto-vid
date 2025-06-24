from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union, Literal, Dict, Any
from enum import Enum


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
    voiceId: str = "Joanna"
    engine: str = "neural"


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


class Output(BaseModel):
    destination: str
    filename: str
    encoding: Optional[Encoding] = None


class JobSpec(BaseModel):
    metadata: Optional[Metadata] = None
    assets: Assets
    backgroundMusic: Optional[BackgroundMusic] = None
    timeline: List[TimelineEvent]
    output: Output

    @field_validator("timeline")
    @classmethod
    def validate_timeline_not_empty(cls, v):
        if not v:
            raise ValueError("Timeline cannot be empty")
        return v