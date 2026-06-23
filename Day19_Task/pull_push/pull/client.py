# =============================================================================
# client.py  ·  Pull Architecture — Polling Client
#
# CONCEPT
#   Client asks the server "any new data?" on a fixed timer.
#   This is called POLLING.
#
# PROS
#   + Simple — just HTTP GET on a timer
#   + Works everywhere — no special infrastructure
#   + Client fully controls the pace
#
# CONS
#   - Wasteful — most requests return nothing
#   - Not real-time — delay equals the poll interval
#   - Server load — many clients polling = constant idle traffic
# =============================================================================

import time
from datetime import datetime
from server import http

POLL_INTERVAL = 2    # seconds between each poll
TOTAL_POLLS   = 8    # stop after this many (demo only)


def run():
    last_seen   = 0
    poll_count  = 0
    empty_polls = 0

    print("=" * 52)
    print("  PULL CLIENT — polling every", POLL_INTERVAL, "seconds")
    print("=" * 52 + "\n")

    while poll_count < TOTAL_POLLS:
        poll_count += 1
        now  = datetime.now().strftime("%H:%M:%S")
        resp = http.get(f"/notifications/new?since_id={last_seen}")
        new  = resp.json()["notifications"]

        if new:
            print(f"[{now}] poll #{poll_count}  ✓  {len(new)} new:")
            for n in new:
                print(f"         [{n['category'].upper()}] {n['message']}")
                last_seen = max(last_seen, n["id"])
        else:
            empty_polls += 1
            print(f"[{now}] poll #{poll_count}  ✗  nothing new  (wasted request)")

        time.sleep(POLL_INTERVAL)

    print(f"\n── Summary ──────────────────────────────────────────")
    print(f"  Total polls    : {poll_count}")
    print(f"  Empty polls    : {empty_polls}  ← wasted bandwidth")
    print(f"  Useful polls   : {poll_count - empty_polls}")
    print(f"  Efficiency     : {round((poll_count-empty_polls)/poll_count*100)}%")
