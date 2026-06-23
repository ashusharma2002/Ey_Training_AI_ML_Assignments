# =============================================================================
# server.py  ·  Pull Architecture — FastAPI Server
#
# CONCEPT
#   Server just sits and waits.
#   Client decides WHEN to ask for data.
#
# ENDPOINTS
#   GET  /notifications/new   client pulls only unseen notifications
#   POST /notify              adds a new notification (simulates an event)
#   GET  /health              server status
# =============================================================================

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Pull Server")

_store      = []
_id_counter = 0


class NotificationIn(BaseModel):
    message:  str
    category: str = "general"


@app.get("/notifications/new")
def get_new(since_id: int = 0):
    """Client pulls only notifications newer than since_id."""
    new = [n for n in _store if n["id"] > since_id]
    return {
        "fetched_at":    datetime.now().isoformat(),
        "new_count":     len(new),
        "notifications": new,
    }


@app.post("/notify")
def add_notification(data: NotificationIn):
    """Simulate an event arriving at the server."""
    global _id_counter
    _id_counter += 1
    _store.append({
        "id":         _id_counter,
        "message":    data.message,
        "category":   data.category,
        "created_at": datetime.now().isoformat(),
    })
    return {"ok": True, "id": _id_counter}


@app.get("/health")
def health():
    return {"status": "ok", "total": len(_store)}


# In-process client — no real server needed
http = TestClient(app)
