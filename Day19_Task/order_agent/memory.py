# ─────────────────────────────────────────────────────────────
# memory.py  ·  Redis memory layer
#
# Gives the agent memory across turns.
#
# Short-term  conversation history  Redis LIST   hist:<session>
# Long-term   user facts / prefs    Redis HASH   facts:<session>
#
# Extensions implemented here
# ─────────────────────────────────────────────────────────────
# Ext 1  compact_if_needed()
#        When history reaches COMPACT_AT turns, the oldest half
#        is summarised by Claude Haiku into one message, keeping
#        the context window bounded forever.
#
# Ext 2  set_fact(ttl_seconds=N)
#        Fact hash auto-expires after N seconds.
#        forget_fact(key) deletes one key immediately.
#
# Ext 6  make_redis()
#        REDIS_URL set in .env  →  real Redis (Upstash / Cloud)
#        REDIS_URL blank        →  fakeredis (no server needed)
#        RedisMemory itself never changes between the two modes.
# ─────────────────────────────────────────────────────────────

import os, json
import fakeredis

COMPACT_AT = 20   # Extension 1: compact when history hits this


def make_redis():
    """Extension 6: real Redis when REDIS_URL is set, otherwise fakeredis."""
    url = os.environ.get("REDIS_URL", "").strip()
    if url:
        import redis
        return redis.Redis.from_url(url)
    return fakeredis.FakeStrictRedis()


class RedisMemory:
    def __init__(self, session_id: str, history_limit: int = 40):
        self.r      = make_redis()
        self.h_key  = f"hist:{session_id}"
        self.f_key  = f"facts:{session_id}"
        self._limit = history_limit

    # ── Short-term ────────────────────────────────────────────

    def append_turn(self, role: str, content):
        self.r.rpush(self.h_key, json.dumps({"role": role, "content": content}))
        self.r.ltrim(self.h_key, -self._limit, -1)

    def load_history(self) -> list[dict]:
        return [json.loads(x) for x in self.r.lrange(self.h_key, 0, -1)]

    def history_len(self) -> int:
        return self.r.llen(self.h_key)

    def overwrite_history(self, turns: list[dict]):
        """Replace the full history list — used by compaction."""
        self.r.delete(self.h_key)
        for t in turns:
            self.r.rpush(self.h_key, json.dumps(t))

    def clear_history(self):
        self.r.delete(self.h_key)

    # ── Long-term ─────────────────────────────────────────────

    def set_fact(self, key: str, value: str, ttl_seconds: int | None = None):
        """Extension 2: ttl_seconds auto-expires the hash."""
        self.r.hset(self.f_key, key, value)
        if ttl_seconds:
            self.r.expire(self.f_key, ttl_seconds)

    def get_fact(self, key: str) -> str | None:
        v = self.r.hget(self.f_key, key)
        return v.decode() if isinstance(v, bytes) else v

    def forget_fact(self, key: str):
        """Extension 2: delete one fact immediately."""
        self.r.hdel(self.f_key, key)

    def all_facts(self) -> dict:
        return {k.decode(): v.decode() for k, v in self.r.hgetall(self.f_key).items()}


def compact_if_needed(mem: RedisMemory, client) -> list[dict]:
    """
    Extension 1 — rolling summary.
    If history >= COMPACT_AT, summarise oldest half with Haiku,
    overwrite Redis, return the compacted message list.
    """
    history = mem.load_history()
    if len(history) < COMPACT_AT:
        return history

    split, recent = len(history) // 2, history[len(history) // 2:]
    text = "\n".join(
        f"{t['role'].upper()}: {t['content'] if isinstance(t['content'], str) else str(t['content'])}"
        for t in history[:split]
    )
    summary = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system="Summarise this conversation in 3-5 sentences. Start with 'Earlier:'.",
        messages=[{"role": "user", "content": text}],
    ).content[0].text

    compacted = [{"role": "assistant", "content": summary}] + recent
    mem.overwrite_history(compacted)
    print(f"  [compact] {len(history)} turns → 1 summary + {len(recent)} recent")
    return compacted
