# =============================================================================
# client.py  ·  Push Architecture — SSE Listener
#
# CONCEPT
#   Client opens ONE connection and waits passively.
#   Events arrive the instant the server sends them.
#   No polling, no timers, no repeated requests.
#
# PROS
#   + Real-time — event arrives the instant it happens
#   + Efficient — one connection, unlimited events, zero wasted requests
#   + Low server load — no idle polling traffic
#
# CONS
#   - More complex server — must manage open connections
#   - Connection can drop — needs reconnect logic in production
#   - Some proxies/firewalls can block persistent connections
# =============================================================================

import json
import httpx
from datetime import datetime

BASE_URL   = "http://localhost:8002"
MAX_EVENTS = 5    # stop after receiving this many (demo only)


async def run(transport=None):
    """
    Connect to SSE stream and print events as they arrive.
    Pass `transport` for in-process testing, leave None for real server.
    """
    request_count = 1    # only ONE HTTP request ever made
    event_count   = 0

    print("=" * 52)
    print("  PUSH CLIENT — connected, waiting for events")
    print("  (zero polling — server will push instantly)")
    print("=" * 52 + "\n")

    kwargs = {"transport": transport, "base_url": "http://test"} if transport \
             else {"base_url": BASE_URL}

    async with httpx.AsyncClient(timeout=None, **kwargs) as client:
        async with client.stream("GET", "/stream") as resp:
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue

                now  = datetime.now().strftime("%H:%M:%S")
                data = json.loads(line[5:].strip())

                if "id" not in data:
                    print(f"[{now}] ✓ connected — waiting for events\n")
                    continue

                event_count += 1
                print(
                    f"[{now}] event #{event_count} received instantly:\n"
                    f"         [{data['category'].upper()}] {data['message']}\n"
                )

                if event_count >= MAX_EVENTS:
                    break

    print(f"── Summary ──────────────────────────────────────────")
    print(f"  HTTP requests  : {request_count}  ← just ONE connection")
    print(f"  Events received: {event_count}")
    print(f"  Wasted requests: 0")
    print(f"  Every event arrived the moment it was created.")
