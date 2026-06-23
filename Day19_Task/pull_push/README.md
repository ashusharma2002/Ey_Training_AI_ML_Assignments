# Pull vs Push Notification Architecture

---

## What this is

Two ways a client receives data from a server — built, demonstrated, and compared.

```
PULL (Polling)                        PUSH (Server-Sent Events)
──────────────────────────────────    ──────────────────────────────────
Client asks on a timer:               Client opens one connection:

Client ── "any news?" ──▶ Server      Client ── open once ──▶ Server
Client ◀── "nope" ──────  Server      Client ◀── event! ────  Server
Client ── "any news?" ──▶ Server      Client ◀── event! ────  Server
Client ◀── "nope" ──────  Server      Client ◀── event! ────  Server
Client ── "any news?" ──▶ Server      (stays open forever)
Client ◀── "event!" ────  Server
```

---

## Structure

```
pull_push/
│
├── pull/
│   ├── server.py     FastAPI — GET /notifications/new + POST /notify
│   ├── client.py     Polling client — asks every N seconds
│   └── run.py        Run the Pull demo
│
├── push/
│   ├── server.py     FastAPI — GET /stream (SSE) + POST /notify
│   ├── client.py     SSE listener — one connection, zero polling
│   └── run.py        Run the Push demo
│
├── compare.py        Run both, print side-by-side results
├── test_all.py       Tests for Pull and Push
├── requirements.txt
└── README.md
```

---

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Run

```bash
# Pull demo
python pull/run.py

# Push demo
python push/run.py

# Side-by-side comparison
python compare.py

# Tests
pytest test_all.py -v
```

---

## Pull — How it works

Client polls on a timer. Server responds with whatever exists at that moment.

```python
# client keeps asking
while True:
    new = GET /notifications/new?since_id={last_seen}
    process(new)
    sleep(3)          # ← delay + wasted requests
```

**Pros** — simple, works everywhere, client controls pace  
**Cons** — wasteful, not real-time, delay = poll interval  
**Use for** — email refresh, analytics dashboards, batch status checks

---

## Push — How it works

Client opens one SSE connection. Server pushes events the instant they happen.

```python
# server streams events as they occur
async def stream(queue):
    while True:
        event = await queue.get()     # waits until something happens
        yield f"data: {event}\n\n"   # pushes instantly

# client just listens
async with client.stream("GET", "/stream") as resp:
    async for line in resp.aiter_lines():
        process(line)                 # no polling, no sleep
```

**Pros** — real-time, zero wasted requests, efficient  
**Cons** — more complex server, connection management needed  
**Use for** — live notifications, chat, stock prices, order tracking

---

## Comparison

| Metric | Pull | Push |
|---|---|---|
| HTTP requests for 4 events | ~7 | 1 |
| Wasted requests | ~4 | 0 |
| Latency | up to poll interval | near zero |
| Server complexity | low | medium |
| Works through all proxies | yes | usually |

---

## Push to GitHub

```bash
git init
git add .
git commit -m "Pull vs Push notification architecture"
git remote add origin https://github.com/YOUR_USERNAME/pull_push.git
git push -u origin main
```
