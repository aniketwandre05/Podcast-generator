import json
import logging
import re
from typing import Any, Dict, List, Optional
from app.sarvam.client import sarvam_client

logger = logging.getLogger("podcastai.llm")

def extract_and_parse_json(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from LLM output with robust repair logic."""
    text = text.strip()
    
    # 1. Direct parse attempt
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Extract from markdown code fences ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            pass

    # 3. Find outermost braces { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            # Common repair: remove trailing commas before closing braces/brackets
            fixed = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(fixed)
            except Exception:
                pass

    raise ValueError(f"Could not extract valid JSON from LLM response: {text[:300]}...")

async def generate_chat_completion(
    messages: List[Dict[str, str]],
    model: str = "sarvam-105b-conversations",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """Invoke Sarvam Chat Completions API."""
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    data = await sarvam_client.post("v1/chat/completions", payload)
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("No completion choices returned by Sarvam LLM.")
    return choices[0]["message"]["content"]

async def generate_structured_json(
    messages: List[Dict[str, str]],
    model: str = "sarvam-105b-conversations",
    temperature: float = 0.6,
    max_tokens: int = 4096,
    max_repair_attempts: int = 2,
) -> Dict[str, Any]:
    """Generate structured JSON from Sarvam LLM with automatic retry-and-repair."""
    current_messages = list(messages)
    
    for attempt in range(max_repair_attempts + 1):
        content = await generate_chat_completion(
            messages=current_messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        try:
            return extract_and_parse_json(content)
        except Exception as e:
            logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
            if attempt == max_repair_attempts:
                raise RuntimeError(f"Failed to produce valid JSON after {max_repair_attempts} repairs: {e}")
            
            # Send repair prompt
            current_messages.append({"role": "assistant", "content": content})
            current_messages.append({
                "role": "user",
                "content": f"Your previous response was not valid JSON ({e}). Output ONLY valid JSON, with no explanation or markdown fences."
            })

