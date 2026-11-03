from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Turn(BaseModel):
    speaker: str = Field(..., description="Speaker identifier (e.g. HOST, CO_HOST, GUEST)")
    text: str = Field(..., description="Spoken dialogue text without stage directions")
    emotion: Optional[str] = Field("natural", description="Tone/emotion tag (e.g. enthusiastic, thoughtful)")
    pause_after_ms: int = Field(350, description="Pause duration after this turn in milliseconds")
    language_code: Optional[str] = Field(None, description="Per-turn language override")
    audio_url: Optional[str] = Field(None, description="URL or path to synthesized audio chunk")

class Segment(BaseModel):
    name: str = Field(..., description="Segment name (e.g. Hook, Deep Dive, Recap)")
    summary: Optional[str] = Field("", description="Short synopsis of the segment")
    turns: List[Turn] = Field(default_factory=list)

class Script(BaseModel):
    title: str = Field(..., description="Catchy episode title")
    description: str = Field(..., description="Show notes summary")
    segments: List[Segment] = Field(default_factory=list)

class OutlineSegment(BaseModel):
    title: str
    goal: str
    key_points: List[str] = Field(default_factory=list)

class Outline(BaseModel):
    title: str
    hook: str
    intro: str
    segments: List[OutlineSegment] = Field(default_factory=list)
    recap: str
    outro: str

class SpeakerConfig(BaseModel):
    speaker_id: str # HOST, CO_HOST, GUEST
    display_name: str
    voice: str # shubh, priya, rohan, etc.
    gender: str = "neutral"
    pace: float = 1.0
    language_code: str = "en-IN"

class EpisodeCreateRequest(BaseModel):
    topic: str
    source_type: str = "prompt" # prompt, document, url
    source_content: Optional[str] = ""
    language: str = "en-IN"
    tone: str = "casual" # casual, educational, debate, interview, storytelling, news-brief
    target_duration_mins: int = 5 # 5, 10, 15, 20
    audience_level: str = "general" # beginner, general, technical, executive
    speakers: List[SpeakerConfig] = Field(default_factory=list)
    background_music: str = "chill_ambient.wav"
    music_volume: float = 0.12
    enable_web_search: bool = False

class EpisodeResponse(BaseModel):
    id: str
    title: str
    description: str
    topic: str
    source_type: str
    language: str
    tone: str
    target_duration_mins: int
    speakers_config: List[Dict[str, Any]]
    research_brief: Dict[str, Any]
    outline: Dict[str, Any]
    script: Dict[str, Any]
    audio_path: Optional[str] = None
    audio_url: Optional[str] = None
    duration_seconds: float
    status: str
    progress_percent: int
    status_message: str
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

class VoicePreviewRequest(BaseModel):
    voice: str
    language_code: str = "en-IN"
    text: Optional[str] = None
    pace: float = 1.0
    model: str = "bulbul:v3"

class ScriptUpdateRequest(BaseModel):
    script: Script

class TranslateEpisodeRequest(BaseModel):
    target_language_code: str # e.g. hi-IN, bn-IN, ta-IN
    mode: str = "modern-colloquial" # formal, modern-colloquial, classic-colloquial, code-mixed

