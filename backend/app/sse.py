import asyncio
import json
from typing import AsyncGenerator
from redis import Redis
from fastapi import Request
from .config import settings

def sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

async def progress_stream(request: Request, analysis_id: str) -> AsyncGenerator[str, None]:
    r = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    channel = f"progress:{analysis_id}"
    pubsub.subscribe(channel)

    try:
        yield sse_event({"type": "connected", "analysis_id": analysis_id})

        while True:
            if await request.is_disconnected():
                break

            msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("type") == "message":
                yield f"data: {msg['data']}\n\n"

            await asyncio.sleep(0.05)

    finally:
        try:
            pubsub.unsubscribe(channel)
            pubsub.close()
        except Exception:
            pass