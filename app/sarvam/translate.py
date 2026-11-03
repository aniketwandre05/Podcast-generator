import logging
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
    """Translate short text snippet using Sarvam Mayura or Sarvam-Translate."""
    text = text.strip()
    if not text:
        return ""

    # Mayura limit is 1000 chars; if longer, use sarvam-translate:v1 or chunk
    if len(text) > 900:
        model = "sarvam-translate:v1"
        mode = "formal"

    payload = {
        "input": text,
        "source_language_code": source_language_code,
        "target_language_code": target_language_code,
        "mode": mode,
        "model": model,
    }

    data = await sarvam_client.post("translate", payload)
    return data.get("translated_text", text)

