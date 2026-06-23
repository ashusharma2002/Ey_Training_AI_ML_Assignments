# =============================================================================
# compare.py  ·  Pull vs Push — side-by-side comparison
#
# Runs both architectures against the same events and prints a table.
#
# python compare.py
# =============================================================================

import sys, os, time, threading, asyncio, json
import httpx
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pull"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "push"))

import pull.server as pull_srv
import push.server as push_srv

EVENTS        = [
    (2,  "Order shipped",       "orders"),
    (5,  "Flash sale live",     "promotions"),
    (9,  "Out for delivery",    "orders"),
    (12, "Delivery confirmed",  "orders"),
]
POLL_INTERVAL = 3
TOTAL_POLLS   = 7


# ── Pull simulation ───────────────────────────────────────────

def simulate_pull() -> dict:
    client      = TestClient(pull_srv.app)
    last_seen   = 0
    polls       = 0
    empty       = 0
    received    = []
    start       = time.time()

    def produce():
        for delay, msg, cat in EVENTS:
            time.sleep(delay)
            client.post("/notify", json={"message": msg, "category": cat})

    threading.Thread(target=produce, daemon=True).start()

    while polls < TOTAL_POLLS:
        polls += 1
        new = client.get(f"/notifications/new?since_id={last_seen}").json()["notifications"]
        if new:
            for n in new:
                received.append(n)
                last_seen = max(last_seen, n["id"])
        else:
            empty += 1
        time.sleep(POLL_INTERVAL)

    return {
        "requests":  polls,
        "wasted":    empty,
        "received":  len(received),
        "efficiency": round((polls - empty) / polls * 100),
    }


# ── Push simulation ───────────────────────────────────────────

async def simulate_push() -> dict:
    transport = httpx.ASGITransport(app=push_srv.app)
    received  = []

    async def produce():
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            for delay, msg, cat in EVENTS:
                await asyncio.sleep(delay)
                await c.post("/notify", json={"message": msg, "category": cat})

    async def listen():
        async with httpx.AsyncClient(transport=transport, base_url="http://test",
                                      timeout=None) as c:
            async with c.stream("GET", "/stream") as resp:
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = json.loads(line[5:].strip())
                    if "id" in data:
                        received.append(data)
                    if len(received) >= len(EVENTS):
                        break

    await asyncio.gather(produce(), listen())
    return {
        "requests":   1,
        "wasted":     0,
        "received":   len(received),
        "efficiency": 100,
    }


# ── Print table ───────────────────────────────────────────────

def print_table(pull: dict, push: dict):
    rows = [
        ("HTTP requests made",    pull["requests"],    push["requests"]),
        ("Wasted requests",       pull["wasted"],      push["wasted"]),
        ("Events received",       pull["received"],    push["received"]),
        ("Request efficiency",    f"{pull['efficiency']}%", f"{push['efficiency']}%"),
    ]

    print("\n" + "="*54)
    print("  PULL vs PUSH — Results")
    print("="*54)
    print(f"  {'Metric':<28} {'PULL':>10}  {'PUSH':>10}")
    print(f"  {'-'*28} {'-'*10}  {'-'*10}")
    for label, p, s in rows:
        print(f"  {label:<28} {str(p):>10}  {str(s):>10}")
    print()
    print(f"  PULL  → {pull['requests']} requests, {pull['wasted']} wasted, "
          f"{pull['efficiency']}% efficient")
    print(f"  PUSH  → {push['requests']} request,  {push['wasted']} wasted, "
          f"{push['efficiency']}% efficient")
    print()
    print(f"  Use PULL when  : simplicity matters, slight delay is OK")
    print(f"  Use PUSH when  : real-time matters, efficiency matters")
    print()


if __name__ == "__main__":
    print("Simulating Pull...")
    pull_result = simulate_pull()

    print("Simulating Push...")
    push_result = asyncio.run(simulate_push())

    print_table(pull_result, push_result)
