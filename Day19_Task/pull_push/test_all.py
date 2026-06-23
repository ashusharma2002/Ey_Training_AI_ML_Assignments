# =============================================================================
# test_all.py  ·  Tests for Pull and Push
# Run:  pytest test_all.py -v
# =============================================================================

import sys, os, asyncio, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pull"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "push"))

import pytest
import httpx
from fastapi.testclient import TestClient

import pull.server as pull_srv
import push.server as push_srv


# ── Pull ──────────────────────────────────────────────────────

@pytest.fixture
def pull():
    return TestClient(pull_srv.app)

class TestPull:
    def test_health(self, pull):
        assert pull.get("/health").status_code == 200

    def test_empty_initially(self, pull):
        r = pull.get("/notifications/new?since_id=0")
        assert r.json()["new_count"] == 0

    def test_add_then_pull(self, pull):
        pull.post("/notify", json={"message": "hello", "category": "test"})
        r = pull.get("/notifications/new?since_id=0").json()
        assert r["new_count"] >= 1
        assert r["notifications"][0]["message"] == "hello"

    def test_since_id_filters(self, pull):
        pull.post("/notify", json={"message": "A", "category": "test"})
        pull.post("/notify", json={"message": "B", "category": "test"})
        all_n   = pull.get("/notifications/new?since_id=0").json()["notifications"]
        last_id = all_n[-1]["id"]
        r       = pull.get(f"/notifications/new?since_id={last_id}").json()
        assert r["new_count"] == 0


# ── Push ──────────────────────────────────────────────────────

class TestPush:
    def test_health(self):
        r = TestClient(push_srv.app).get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_notify_endpoint(self):
        r = TestClient(push_srv.app).post(
            "/notify", json={"message": "test", "category": "test"}
        )
        assert r.json()["ok"] is True

    @pytest.mark.asyncio
    async def test_push_delivers_to_subscriber(self):
        transport = httpx.ASGITransport(app=push_srv.app)
        received  = []

        async def listen():
            async with httpx.AsyncClient(transport=transport,
                                          base_url="http://test", timeout=5) as c:
                async with c.stream("GET", "/stream") as resp:
                    async for line in resp.aiter_lines():
                        if line.startswith("data:"):
                            data = json.loads(line[5:].strip())
                            if "id" in data:
                                received.append(data)
                                break

        async def send():
            await asyncio.sleep(0.3)
            async with httpx.AsyncClient(transport=transport,
                                          base_url="http://test") as c:
                await c.post("/notify", json={"message": "pushed!", "category": "test"})

        await asyncio.gather(listen(), send())
        assert len(received) == 1
        assert received[0]["message"] == "pushed!"
