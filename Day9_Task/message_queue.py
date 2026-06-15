import nest_asyncio
nest_asyncio.apply()

print("Ready")

import asyncio
import json
import uuid
import time
import random
import threading
import structlog
import uvicorn
import httpx

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

from pyngrok import ngrok, conf
from prometheus_client import Gauge

# =========================================================
# LOGGING
# =========================================================

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger()

# =========================================================
# MESSAGE MODEL
# =========================================================

@dataclass
class Message:

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    body: Dict[str, Any] = field(default_factory=dict)

    delivery_count: int = 0

    dead_lettered_at: Optional[str] = None

    dead_letter_reason: Optional[str] = None

# =========================================================
# BROKER
# =========================================================

class Broker:

    def __init__(self):

        self.queues = {
            "payments": asyncio.Queue(),
            "payments.dlq": asyncio.Queue(),
        }

        self.stats = {
            "published": 0,
            "consumed": 0,
            "dead_lettered": 0
        }

    async def publish(self, queue_name: str, body: dict):

        msg = Message(body=body)

        await self.queues[queue_name].put(msg)

        self.stats["published"] += 1

        log.info(
            "mq.published",
            queue=queue_name,
            message_id=msg.id,
            body=body
        )

        return msg.id

    async def consume(self, queue_name: str):

        try:

            return self.queues[queue_name].get_nowait()

        except asyncio.QueueEmpty:

            return None

    async def dead_letter(self, msg: Message, reason: str):

        msg.dead_lettered_at = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime()
        )

        msg.dead_letter_reason = reason

        await self.queues["payments.dlq"].put(msg)

        self.stats["dead_lettered"] += 1

        log.warning(
            "mq.dead_lettered",
            message_id=msg.id,
            reason=reason
        )

    def depth(self, queue_name: str):

        return self.queues[queue_name].qsize()

broker = Broker()

print("In-memory broker ready — queues: payments, payments.dlq")

# =========================================================
# FASTAPI
# =========================================================

class PaymentRequest(BaseModel):

    amount: float = Field(..., gt=0)

    currency: str = Field(default="GBP")

    account_id: str

    reference: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):

    log.info(
        "app.startup",
        message="Connecting to broker..."
    )

    yield

    log.info(
        "app.shutdown",
        message="Disconnecting from broker..."
    )

app = FastAPI(
    title="EY Payment Queue API",
    version="2.0.0",
    lifespan=lifespan
)

# =========================================================
# PAYMENTS API
# =========================================================

@app.post("/payments", status_code=202)
async def enqueue_payment(payment: PaymentRequest):

    msg_id = await broker.publish(
        "payments",
        payment.model_dump()
    )

    return {
        "message_id": msg_id,
        "status": "queued",
        "queue_depth": broker.depth("payments")
    }

print("Producer endpoint /payments defined")

# =========================================================
# WORKER
# =========================================================

MAX_DELIVERIES = 3

async def process_payment(msg: Message):

    await asyncio.sleep(0.05)

    if random.random() < 0.4:

        raise ValueError(
            f'Processor timeout for {msg.body.get("account_id")}'
        )

    return {
        "processed_id": str(uuid.uuid4()),
        "status": "settled"
    }

async def worker_tick():

    msg = await broker.consume("payments")

    if msg is None:

        return None

    msg.delivery_count += 1

    log.info(
        "worker.processing",
        message_id=msg.id,
        delivery_count=msg.delivery_count
    )

    try:

        result = await process_payment(msg)

        broker.stats["consumed"] += 1

        log.info(
            "worker.acked",
            message_id=msg.id
        )

        return {
            "acked": msg.id,
            "result": result
        }

    except Exception as e:

        if msg.delivery_count >= MAX_DELIVERIES:

            await broker.dead_letter(
                msg,
                str(e)
            )

            return {
                "dead_lettered": msg.id
            }

        else:

            await asyncio.sleep(
                0.5 * msg.delivery_count
            )

            await broker.queues["payments"].put(msg)

            log.warning(
                "worker.nacked",
                message_id=msg.id
            )

            return {
                "nacked": msg.id
            }

@app.get("/payments/worker")
async def drain_one():

    result = await worker_tick()

    if result is None:

        return {
            "status": "queue_empty"
        }

    return result

print("Consumer worker + /payments/worker endpoint defined")

# =========================================================
# HEALTH
# =========================================================

@app.get("/health/live")
async def liveness():

    return {
        "status": "alive"
    }

@app.get("/health/ready")
async def readiness():

    return JSONResponse(
        content={
            "status": "ready",
            "mq": "ok",
            "db": "ok",
            "queue_depth": broker.depth("payments")
        },
        status_code=200
    )

print("Health endpoints defined")

# =========================================================
# ADMIN
# =========================================================

@app.get("/admin/dlq")
async def inspect_dlq(limit: int = Query(default=10, le=50)):

    items = []

    temp = []

    while len(items) < limit:

        msg = await broker.consume("payments.dlq")

        if msg is None:

            break

        items.append({
            "id": msg.id,
            "body": msg.body,
            "delivery_count": msg.delivery_count,
            "reason": msg.dead_letter_reason
        })

        temp.append(msg)

    for m in temp:

        await broker.queues["payments.dlq"].put(m)

    return {
        "dlq_depth": broker.depth("payments.dlq"),
        "messages": items
    }

@app.post("/admin/dlq/retry")
async def replay_dlq(limit: int = Query(default=5, le=20)):

    replayed = []

    for _ in range(limit):

        msg = await broker.consume("payments.dlq")

        if msg is None:

            break

        msg.delivery_count = 0

        await broker.queues["payments"].put(msg)

        replayed.append(msg.id)

    return {
        "replayed": len(replayed),
        "message_ids": replayed
    }

@app.get("/admin/stats")
async def queue_stats():

    return {
        **broker.stats,
        "payments_depth": broker.depth("payments"),
        "dlq_depth": broker.depth("payments.dlq")
    }

print("Admin endpoints defined")

# =========================================================
# EXTENSION B — SERVICE BUS
# =========================================================

SERVICE_BUS_QUEUE = asyncio.Queue()

SERVICE_BUS_DLQ = asyncio.Queue()

async def servicebus_publish(payment):

    await SERVICE_BUS_QUEUE.put(payment)

    return {
        "status": "queued",
        "service_bus": "working"
    }

@app.post("/servicebus/payments")
async def servicebus_payment(payment: PaymentRequest):

    return await servicebus_publish(
        payment.model_dump()
    )

@app.get("/servicebus/worker")
async def servicebus_worker():

    try:

        payment = SERVICE_BUS_QUEUE.get_nowait()

    except asyncio.QueueEmpty:

        return {
            "status": "empty"
        }

    try:

        if random.random() < 0.4:

            raise Exception("Service Bus processing failed")

        return {
            "status": "processed",
            "payment": payment
        }

    except Exception as e:

        await SERVICE_BUS_DLQ.put(payment)

        return {
            "status": "dead_lettered",
            "reason": str(e)
        }

@app.get("/servicebus/dlq")
async def servicebus_dlq():

    return {
        "dlq_depth": SERVICE_BUS_DLQ.qsize()
    }

print("Extension B Loaded")

# =========================================================
# EXTENSION C — PRIORITY QUEUE
# =========================================================

HIGH_PRIORITY_QUEUE = asyncio.PriorityQueue()

async def publish_priority_payment(payment):

    priority = 8 if payment["amount"] > 10000 else 3

    await HIGH_PRIORITY_QUEUE.put(
        (
            -priority,
            {
                "priority": priority,
                "payment": payment
            }
        )
    )

    return {
        "status": "queued",
        "priority": priority
    }

@app.post("/priority-payments")
async def priority_payment(payment: PaymentRequest):

    return await publish_priority_payment(
        payment.model_dump()
    )

@app.get("/priority-worker")
async def process_priority_payment():

    if HIGH_PRIORITY_QUEUE.empty():

        return {
            "status": "empty"
        }

    _, item = await HIGH_PRIORITY_QUEUE.get()

    return {
        "processed": item
    }

print("Extension C Loaded")

# =========================================================
# EXTENSION D — BACKGROUND WORKER
# =========================================================

DLQ_DEPTH_GAUGE = Gauge(
    "dlq_depth",
    "Dead Letter Queue Depth"
)

async def background_worker():

    while True:

        await worker_tick()

        depth = broker.depth("payments.dlq")

        DLQ_DEPTH_GAUGE.set(depth)

        if depth > 10:

            print("CRITICAL ALERT")

        await asyncio.sleep(1)

@app.on_event("startup")
async def start_background_worker():

    asyncio.create_task(
        background_worker()
    )

print(" Extension D Loaded")

# =========================================================
# NGROK
# =========================================================

NGROK_TOKEN = "3Et08KLYiQGjHkwaSzcMTEL3o8k_4rZRSZqSLSM8aS5g9TqJQ"

conf.get_default().auth_token = NGROK_TOKEN

ngrok.kill()

PORT = 8010

def run_server():

    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=PORT,
        log_level="warning"
    )

    server = uvicorn.Server(config)

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    loop.run_until_complete(
        server.serve()
    )

thread = threading.Thread(
    target=run_server,
    daemon=True
)

thread.start()

time.sleep(3)

tunnel = ngrok.connect(PORT)

BASE = tunnel.public_url

print(f"🌐 {BASE}")

print(f"Docs: {BASE}/docs")

# =========================================================
# TESTING
# =========================================================

with httpx.Client() as c:

    print("\n--- HEALTH ---")

    print(
        c.get(
            f"{BASE}/health/ready"
        ).json()
    )

    print("\n--- PAYMENT TEST ---")

    for i in range(5):

        r = c.post(
            f"{BASE}/payments",
            json={
                "amount": (i+1)*100,
                "currency": "GBP",
                "account_id": f"ACC-{i+1:03}"
            }
        )

        print(r.json())

    print("\n--- WORKER TEST ---")

    for _ in range(10):

        print(
            c.get(
                f"{BASE}/payments/worker"
            ).json()
        )

    print("\n--- EXTENSION B TEST ---")

    print(
        c.post(
            f"{BASE}/servicebus/payments",
            json={
                "amount": 1200,
                "currency": "GBP",
                "account_id": "SB-001"
            }
        ).json()
    )

    print(
        c.get(
            f"{BASE}/servicebus/worker"
        ).json()
    )

    print(
        c.get(
            f"{BASE}/servicebus/dlq"
        ).json()
    )

    print("\n--- EXTENSION C TEST ---")

    print(
        c.post(
            f"{BASE}/priority-payments",
            json={
                "amount": 500,
                "currency": "GBP",
                "account_id": "LOW-001"
            }
        ).json()
    )

    print(
        c.post(
            f"{BASE}/priority-payments",
            json={
                "amount": 25000,
                "currency": "GBP",
                "account_id": "HIGH-001"
            }
        ).json()
    )

    print(
        c.get(
            f"{BASE}/priority-worker"
        ).json()
    )

    print(
        c.get(
            f"{BASE}/priority-worker"
        ).json()
    )

    print("\n--- FINAL STATS ---")

    print(
        c.get(
            f"{BASE}/admin/stats"
        ).json()
    )

print("\n Extension B + C + D Completed Successfully")
