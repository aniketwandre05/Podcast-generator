import logging
import re
from typing import Dict, List, Optional
from app.sarvam.client import sarvam_client

logger = logging.getLogger("podcastai.translate")

async def translate_text(
    text: str,
    source_language_code: str = "en-IN",
    target_language_code: str = "hi-IN",
    mode: str = "modern-colloquial",
    model: str = "mayura:v1",
) -> str:
    """Translate text snippet using Sarvam Mayura or Sarvam-Translate."""
    text = text.strip()
    if not text:
        return ""

    # If source and target language are identical, return as is
    if source_language_code == target_language_code:
        return text

    # Mayura limit is ~1000 chars; if longer, chunk or use sarvam-translate:v1
    if len(text) > 900:
        # Split on sentence boundaries and translate each
        sentences = re.split(r"(?<=[.?!।\n])\s+", text)
        translated_chunks = []
        for s in sentences:
            if not s.strip():
                continue
            chunk_res = await translate_text(
                text=s,
                source_language_code=source_language_code,
                target_language_code=target_language_code,
                mode=mode,
                model=model,
            )
            translated_chunks.append(chunk_res)
        return " ".join(translated_chunks)

    payload = {
        "input": text,
        "source_language_code": source_language_code,
        "target_language_code": target_language_code,
        "mode": mode,
        "model": model,
    }

    try:
        data = await sarvam_client.post("translate", payload)
        return data.get("translated_text", text)
    except Exception as e:
        logger.warning(f"Translation failed for '{text[:40]}...': {e}")
        return text

