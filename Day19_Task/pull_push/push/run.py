# =============================================================================
# run.py  ·  Push Demo — run this file
#
# Runs server + client together using asyncio.
# Event producer fires events at set times.
# SSE client receives each one instantly.
#
# python push/run.py
# =============================================================================

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import httpx
from server import app
from client import run as listen

EVENTS = [
    (2,  "Order #A1001 has shipped",          "orders"),
    (4,  "Flash sale: 20% off monitors",      "promotions"),
    (6,  "Order #A1002 out for delivery",     "orders"),
    (8,  "Your review request for A1001",     "feedback"),
    (10, "Exclusive Gold member offer",       "promotions"),
]


async def produce_events(transport):
    """Fires events at set times to simulate real-world activity."""
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for delay, message, category in EVENTS:
            await asyncio.sleep(delay)
            await client.post("/notify", json={"message": message, "category": category})
            print(f"  [event fired] {message}")


async def main():
    transport = httpx.ASGITransport(app=app)
    await asyncio.gather(
        produce_events(transport),
        listen(transport=transport),
    )


if __name__ == "__main__":
    asyncio.run(main())
