import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.core.database import Base

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), default="Untitled Podcast")
    description = Column(Text, default="")
    topic = Column(Text, nullable=False)
    source_type = Column(String(50), default="prompt") # prompt, document, url
    source_content = Column(Text, default="")
    
    language = Column(String(20), default="en-IN")
    tone = Column(String(50), default="casual") # casual, educational, debate, interview, storytelling, news-brief
    target_duration_mins = Column(Integer, default=5)
    audience_level = Column(String(50), default="general")
    
    # JSON strings
    _speakers_config = Column("speakers_config", Text, default="[]")
    _research_brief = Column("research_brief", Text, default="{}")
    _outline = Column("outline", Text, default="{}")
    _script = Column("script", Text, default="{}")
    
    # Music & Audio
    background_music = Column(String(100), default="chill_ambient.wav")
    music_volume = Column(Float, default=0.12)
    audio_path = Column(String(500), nullable=True)
    duration_seconds = Column(Float, default=0.0)
    
    # Status & Progress
    status = Column(String(50), default="created") # created, researching, outlining, writing, review_script, synthesizing, mixing, completed, failed
    progress_percent = Column(Integer, default=0)
    status_message = Column(String(255), default="Initialized")
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def speakers_config(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self._speakers_config) if self._speakers_config else []
        except Exception:
            return []

    @speakers_config.setter
    def speakers_config(self, val: List[Dict[str, Any]]):
        self._speakers_config = json.dumps(val)

    @property
    def research_brief(self) -> Dict[str, Any]:
        try:
            return json.loads(self._research_brief) if self._research_brief else {}
        except Exception:
            return {}

    @research_brief.setter
    def research_brief(self, val: Dict[str, Any]):
        self._research_brief = json.dumps(val)

    @property
    def outline(self) -> Dict[str, Any]:
        try:
            return json.loads(self._outline) if self._outline else {}
        except Exception:
            return {}

    @outline.setter
    def outline(self, val: Dict[str, Any]):
        self._outline = json.dumps(val)

    @property
    def script(self) -> Dict[str, Any]:
        try:
            return json.loads(self._script) if self._script else {}
        except Exception:
            return {}

    @script.setter
    def script(self, val: Dict[str, Any]):
        self._script = json.dumps(val)

