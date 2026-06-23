# =============================================================================
# server.py  ·  Push Architecture — FastAPI SSE Server
#
# CONCEPT
#   Server pushes data to clients the moment something happens.
#   Client opens ONE connection and just listens.
#   No polling needed.
#
# TECHNOLOGY: Server-Sent Events (SSE)
#   Client opens a persistent HTTP connection.
#   Server streams events down that connection as they occur.
#
# ENDPOINTS
#   GET  /stream    client connects once, receives all future events
#   POST /notify    triggers an event — pushed to ALL connected clients
#   GET  /health    server status
# =============================================================================

import asyncio
import json
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="Push Server (SSE)")

_subscribers: list[asyncio.Queue] = []
_store       = []
_id_counter  = 0


class NotificationIn(BaseModel):
    message:  str
    category: str = "general"


async def _stream(queue: asyncio.Queue):
    """Keeps the connection open and yields events as they arrive."""
    yield 'event: connected\ndata: {"status": "subscribed"}\n\n'
    try:
        while True:
            event = await queue.get()
            yield f"event: notification\ndata: {json.dumps(event)}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        if queue in _subscribers:
            _subscribers.remove(queue)


@app.get("/stream")
async def subscribe():
    """Client connects here ONCE and receives all future events instantly."""
    queue = asyncio.Queue()
    _subscribers.append(queue)
    print(f"  [server] client connected  (active: {len(_subscribers)})")
    return StreamingResponse(
        _stream(queue),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@app.post("/notify")
async def notify(data: NotificationIn):
    """Push an event to ALL connected clients the instant it happens."""
    global _id_counter
    _id_counter += 1
    event = {
        "id":        _id_counter,
        "message":   data.message,
        "category":  data.category,
        "pushed_at": datetime.now().isoformat(),
    }
    _store.append(event)
    for q in _subscribers:
        await q.put(event)
    print(f"  [server] pushed #{_id_counter} to {len(_subscribers)} client(s)")
    return {"ok": True, "id": _id_counter, "delivered_to": len(_subscribers)}


@app.get("/health")
def health():
    return {"status": "ok", "subscribers": len(_subscribers), "total": len(_store)}
