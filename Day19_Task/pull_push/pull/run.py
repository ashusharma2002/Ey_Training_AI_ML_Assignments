# =============================================================================
# run.py  ·  Pull Demo — run this file
#
# Starts a background thread that produces events at set times,
# while the main thread runs the polling client.
#
# python pull/run.py
# =============================================================================

import time
import threading
from server import http
from client import run

EVENTS = [
    (3,  "Order #A1001 has shipped",          "orders"),
    (6,  "Flash sale: 20% off monitors",      "promotions"),
    (11, "Order #A1002 out for delivery",     "orders"),
    (14, "Your review request for A1001",     "feedback"),
]


def produce_events():
    """Adds notifications at fixed times to simulate real events."""
    for delay, message, category in EVENTS:
        time.sleep(delay)
        http.post("/notify", json={"message": message, "category": category})
        print(f"  [event created] {message}")


if __name__ == "__main__":
    # Start event producer in background
    threading.Thread(target=produce_events, daemon=True).start()
    # Run polling client in foreground
    run()
