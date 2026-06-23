# ─────────────────────────────────────────────────────────────
# test_agent.py  ·  Full test suite
#
# Covers base task + all 6 extensions. No API key needed.
# Run:  pytest test_agent.py -v
# ─────────────────────────────────────────────────────────────

import os, time
import pytest
import fakeredis

from api    import http
from memory import RedisMemory
from tools  import make_dispatch, run_tool, _is_pii


# ── API ───────────────────────────────────────────────────────

class TestAPI:
    def test_order_ok(self):
        assert http.get("/orders/A1001").json()["item"] == "Mechanical keyboard"

    def test_order_missing(self):
        assert http.get("/orders/A9999").status_code == 404

    def test_order_case(self):
        assert http.get("/orders/a1002").status_code == 200

    def test_customer_ok(self):                        # Ext 3
        assert http.get("/customers/C01").json()["name"] == "Asha Sharma"

    def test_customer_missing(self):                   # Ext 3
        assert http.get("/customers/C99").status_code == 404


# ── Memory ────────────────────────────────────────────────────

@pytest.fixture
def mem():
    return RedisMemory("test")

class TestMemory:
    def test_history(self, mem):
        mem.append_turn("user", "hi")
        mem.append_turn("assistant", "hello")
        assert len(mem.load_history()) == 2

    def test_history_limit(self):
        m = RedisMemory.__new__(RedisMemory)
        m.r, m._limit = fakeredis.FakeStrictRedis(), 3
        m.h_key, m.f_key = "hist:lim", "facts:lim"
        for i in range(6):
            m.append_turn("user", str(i))
        assert m.history_len() == 3

    def test_facts(self, mem):
        mem.set_fact("k", "v")
        assert mem.get_fact("k") == "v"

    def test_missing_fact(self, mem):
        assert mem.get_fact("nope") is None

    def test_forget(self, mem):                        # Ext 2
        mem.set_fact("k", "v")
        mem.forget_fact("k")
        assert mem.get_fact("k") is None

    def test_ttl(self):                                # Ext 2
        m = RedisMemory("ttl")
        m.set_fact("x", "y", ttl_seconds=1)
        assert m.get_fact("x") == "y"
        time.sleep(1.1)
        assert m.get_fact("x") is None

    def test_overwrite(self, mem):                     # Ext 1
        for i in range(4):
            mem.append_turn("user", str(i))
        mem.overwrite_history([{"role": "assistant", "content": "summary"}])
        assert mem.history_len() == 1

    def test_clear(self, mem):
        mem.append_turn("user", "hi")
        mem.clear_history()
        assert mem.load_history() == []


# ── Tools ─────────────────────────────────────────────────────

@pytest.fixture
def dispatch():
    return make_dispatch(RedisMemory("tools"))

class TestTools:
    def test_get_order(self, dispatch):
        out, err = run_tool(dispatch, "get_order", {"order_id": "A1001"})
        assert not err and out["status"] == "shipped"

    def test_get_order_missing(self, dispatch):
        _, err = run_tool(dispatch, "get_order", {"order_id": "A9999"})
        assert err

    def test_get_customer(self, dispatch):             # Ext 3
        out, err = run_tool(dispatch, "get_customer", {"customer_id": "C01"})
        assert not err and out["tier"] == "gold"

    def test_remember_recall(self, dispatch):
        run_tool(dispatch, "remember_fact", {"key": "s", "value": "express"})
        out, err = run_tool(dispatch, "recall_fact", {"key": "s"})
        assert not err and out["value"] == "express"

    def test_forget(self, dispatch):                   # Ext 2
        run_tool(dispatch, "remember_fact", {"key": "x", "value": "y"})
        run_tool(dispatch, "forget_fact",   {"key": "x"})
        out, _ = run_tool(dispatch, "recall_fact", {"key": "x"})
        assert out["value"] is None

    def test_unknown_tool(self, dispatch):
        _, err = run_tool(dispatch, "nope", {})
        assert err


# ── PII guard (Ext 4) ─────────────────────────────────────────

@pytest.mark.parametrize("value, blocked", [
    ("4111111111111111",    True),
    ("4111 1111 1111 1111", True),
    ("user@example.com",   True),
    ("9876543210",         True),
    ("leave at door",      False),
    ("express",            False),
    ("500",                False),
])
def test_pii(value, blocked):
    is_pii, _ = _is_pii(value)
    assert is_pii == blocked

def test_pii_blocks_store(dispatch):                   # Ext 4
    _, err = run_tool(dispatch, "remember_fact", {"key": "c", "value": "4111111111111111"})
    assert err

def test_safe_stores(dispatch):
    _, err = run_tool(dispatch, "remember_fact", {"key": "n", "value": "leave at door"})
    assert not err


# ── Real Redis (Ext 6) ────────────────────────────────────────

def test_redis_mode():
    from memory import make_redis
    r   = make_redis()
    url = os.environ.get("REDIS_URL", "").strip()
    if url:
        import redis
        assert isinstance(r, redis.Redis)
    else:
        assert isinstance(r, fakeredis.FakeStrictRedis)
