import asyncio
import logging
import random
from typing import Any, Dict, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("podcastai.sarvam")

class SarvamAPIClient:
    BASE_URL = "https://api.sarvam.ai"

    def __init__(self, api_key: Optional[str] = None, transport: Optional[httpx.AsyncBaseTransport] = None):
        self.api_key = api_key or settings.SARVAM_API_KEY
        self.transport = transport
        self.headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "PodcastAI/1.0",
        }
        self.timeout = httpx.Timeout(120.0, connect=15.0)

    async def post(
        self,
        endpoint: str,
        json_data: Dict[str, Any],
        max_retries: int = 4,
        base_delay: float = 1.5,
    ) -> Dict[str, Any]:
        """Make an async POST request to Sarvam with exponential backoff on 429/5xx."""
        url = f"{self.BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
            for attempt in range(max_retries):
                try:
                    response = await client.post(url, headers=self.headers, json=json_data)
                    
                    if response.status_code == 200:
                        return response.json()

                    if response.status_code in [429, 500, 502, 503, 504]:
                        retry_after = response.headers.get("Retry-After")
                        delay = float(retry_after) if retry_after else (base_delay * (2 ** attempt)) + random.uniform(0.1, 0.5)
                        logger.warning(
                            f"Sarvam API {endpoint} returned {response.status_code}. "
                            f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue

                    # Other client errors (400, 401, 403, 404, etc.)
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("message") or error_json.get("detail") or str(error_json)
                    except Exception:
                        pass
                    raise RuntimeError(f"Sarvam API Error ({response.status_code}) on {endpoint}: {error_detail}")

                except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as exc:
                    delay = (base_delay * (2 ** attempt)) + random.uniform(0.1, 0.5)
                    logger.warning(f"Network error on {endpoint}: {exc}. Retrying in {delay:.2f}s...")
                    if attempt == max_retries - 1:
                        raise RuntimeError(f"Network connection failed to Sarvam API: {exc}")
                    await asyncio.sleep(delay)

        raise RuntimeError(f"Sarvam API {endpoint} failed after {max_retries} attempts.")

sarvam_client = SarvamAPIClient()

