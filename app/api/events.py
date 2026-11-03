import asyncio
import json
import logging
from fastapi import APIRouter
from starlette.responses import StreamingResponse
from app.pipeline.generator import subscribe_to_episode, unsubscribe_from_episode

router = APIRouter(tags=["events"])
logger = logging.getLogger("podcastai.events")

@router.get("/api/episodes/{episode_id}/events")
async def stream_episode_events(episode_id: str):
    """Server-Sent Events endpoint streaming real-time pipeline status."""
    queue = subscribe_to_episode(episode_id)

    async def event_generator():
        # Initial ping
        yield f"event: connected\ndata: {json.dumps({'episode_id': episode_id})}\n\n"
        try:
            while True:
                try:
                    # Timeout after 25 seconds of silence to send heartbeat
                    item = await asyncio.wait_for(queue.get(), timeout=25.0)
                    event_type = item.get("type", "message")
                    data_str = json.dumps(item.get("data", {}))
                    yield f"event: {event_type}\ndata: {data_str}\n\n"

                    # If completed or error, finish stream
                    if event_type in ["completed", "error"]:
                        break
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            unsubscribe_from_episode(episode_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

