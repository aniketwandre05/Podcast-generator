import asyncio
import base64
import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from app.core.config import settings
from app.sarvam.client import sarvam_client

logger = logging.getLogger("podcastai.tts")

# Concurrency semaphore for TTS (4 concurrent calls as specified)
tts_semaphore = asyncio.Semaphore(4)

# Sentence split pattern for Indian & English text
SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.?!।|])\s+")

def chunk_text_by_sentence(text: str, max_chars: int = 2000) -> List[str]:
    """Split text along sentence boundaries to respect Sarvam character limits."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    sentences = SENTENCE_SPLIT_REGEX.split(text)
    chunks = []
    current_chunk = []
    current_len = 0

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        
        # If a single sentence is longer than max_chars, split by clause/commas
        if len(sent) > max_chars:
            words = sent.split(" ")
            sub_chunk = []
            sub_len = 0
            for w in words:
                if sub_len + len(w) + 1 > max_chars:
                    chunks.append(" ".join(sub_chunk))
                    sub_chunk = [w]
                    sub_len = len(w)
                else:
                    sub_chunk.append(w)
                    sub_len += len(w) + 1
            if sub_chunk:
                chunks.append(" ".join(sub_chunk))
            continue

        if current_len + len(sent) + 1 > max_chars:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sent]
            current_len = len(sent)
        else:
            current_chunk.append(sent)
            current_len += len(sent) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def compute_tts_cache_key(
    text: str,
    voice: str,
    language_code: str,
    pace: float,
    model: str = "bulbul:v3",
) -> str:
    """Generate deterministic hash for caching TTS results."""
    raw = f"{text.strip()}|{voice.lower()}|{language_code}|{pace:.2f}|{model}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

async def synthesize_chunk(
    text: str,
    voice: str,
    language_code: str = "en-IN",
    pace: float = 1.0,
    model: str = "bulbul:v3",
) -> bytes:
    """Synthesize a single text chunk with caching and concurrency control."""
    cache_key = compute_tts_cache_key(text, voice, language_code, pace, model)
    cache_file = settings.CACHE_DIR / f"{cache_key}.wav"

    # Check cache first
    if cache_file.exists():
        logger.info(f"TTS Cache HIT for '{text[:30]}...' ({voice})")
        return cache_file.read_bytes()

    logger.info(f"TTS Cache MISS. Synthesizing '{text[:30]}...' ({voice})")
    
    payload = {
        "text": text,
        "language_code": language_code,
        "speaker": voice.lower(),
        "pace": pace,
        "model": model,
        "output_audio_codec": "wav",
    }

    async with tts_semaphore:
        data = await sarvam_client.post("text-to-speech", payload)

    audios = data.get("audios", [])
    if not audios:
        raise RuntimeError(f"Sarvam TTS returned empty audio for text: {text[:50]}")

    audio_bytes = base64.b64decode(audios[0])
    
    # Save to disk cache
    cache_file.write_bytes(audio_bytes)
    return audio_bytes

async def synthesize_turn_text(
    text: str,
    voice: str,
    language_code: str = "en-IN",
    pace: float = 1.0,
    model: str = "bulbul:v3",
) -> List[bytes]:
    """Synthesize a full dialogue turn, handling chunking if needed."""
    chunks = chunk_text_by_sentence(text, max_chars=2000)
    audio_chunks = []
    for chunk in chunks:
        audio = await synthesize_chunk(
            text=chunk,
            voice=voice,
            language_code=language_code,
            pace=pace,
            model=model,
        )
        audio_chunks.append(audio)
    return audio_chunks

