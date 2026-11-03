import asyncio
import httpx
from app.sarvam.client import SarvamAPIClient

def test_sarvam_client_success():
    async def _test():
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"status": "ok", "choices": [{"message": {"content": "mock"}}]})

        transport = httpx.MockTransport(handler)
        client = SarvamAPIClient(api_key="mock_key", transport=transport)
        res = await client.post("v1/chat/completions", {"test": 1})
        assert res["status"] == "ok"
        assert res["choices"][0]["message"]["content"] == "mock"

    asyncio.run(_test())

def test_sarvam_client_retry_on_429():
    async def _test():
        attempts = 0
        async def handler(request: httpx.Request) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return httpx.Response(429, headers={"Retry-After": "0.01"})
            return httpx.Response(200, json={"audios": ["mock_base64"]})

        transport = httpx.MockTransport(handler)
        client = SarvamAPIClient(api_key="mock_key", transport=transport)
        res = await client.post("text-to-speech", {"text": "hello"}, max_retries=3, base_delay=0.01)
        assert "audios" in res
        assert attempts == 2

    asyncio.run(_test())
