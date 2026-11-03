from datetime import datetime
from sqlalchemy import Column, DateTime, Float, String, Text
from app.core.database import Base

class VoiceProfile(Base):
    __tablename__ = "voice_profiles"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    role_description = Column(String(255), default="")
    gender = Column(String(20), default="neutral")
    voice_id = Column(String(50), nullable=False) # e.g. shubh, priya, rohan
    language_code = Column(String(20), default="en-IN")
    pace = Column(Float, default=1.0)
    pitch = Column(Float, default=0.0)
    loudness = Column(Float, default=1.0)
    model = Column(String(50), default="bulbul:v3")
    created_at = Column(DateTime, default=datetime.utcnow)

class TTSCache(Base):
    __tablename__ = "tts_cache"

    hash_key = Column(String(64), primary_key=True) # sha256
    text = Column(Text, nullable=False)
    voice_id = Column(String(50), nullable=False)
    language_code = Column(String(20), nullable=False)
    pace = Column(Float, default=1.0)
    model = Column(String(50), default="bulbul:v3")
    audio_path = Column(String(500), nullable=False)
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

