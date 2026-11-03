import os
import sys
from pathlib import Path
from typing import List
try:
    from pydantic_settings import BaseSettings
except ImportError:
    BaseSettings = object

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = DATA_DIR / "storage"
CACHE_DIR = DATA_DIR / "tts_cache"
MUSIC_DIR = BASE_DIR / "assets" / "music"
SAMPLES_DIR = BASE_DIR / "samples"

for d in [DATA_DIR, STORAGE_DIR, CACHE_DIR, MUSIC_DIR, SAMPLES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

class Settings:
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    STORAGE_DIR = STORAGE_DIR
    CACHE_DIR = CACHE_DIR
    MUSIC_DIR = MUSIC_DIR
    SAMPLES_DIR = SAMPLES_DIR

    # Load .env file
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    val = v.strip().strip("'\"")
                    if val and k.strip() not in os.environ:
                        os.environ[k.strip()] = val

    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    
    # Startup validation
    @classmethod
    def validate_api_key(cls):
        if not cls.SARVAM_API_KEY or cls.SARVAM_API_KEY.startswith("your_"):
            print("\n" + "=" * 60, file=sys.stderr)
            print("ERROR: SARVAM_API_KEY is missing or invalid!", file=sys.stderr)
            print("Please set your API key in .env or via the environment.", file=sys.stderr)
            print("=" * 60 + "\n", file=sys.stderr)
            raise RuntimeError("SARVAM_API_KEY is not configured. Backend cannot start.")

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/podcastai.db")
    
    CORS_ORIGINS: List[str] = [
        origin.strip() for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
        ).split(",") if origin.strip()
    ]

    # Sarvam defaults
    DEFAULT_LLM_MODEL: str = "sarvam-105b-conversations"
    DEFAULT_REASONING_MODEL: str = "sarvam-105b"
    DEFAULT_TTS_MODEL: str = "bulbul:v3"
    DEFAULT_TTS_LANGUAGE: str = "en-IN"
    DEFAULT_SPEAKER_1: str = "shubh"
    DEFAULT_SPEAKER_2: str = "priya"
    DEFAULT_SPEAKER_3: str = "rohan"

settings = Settings()
