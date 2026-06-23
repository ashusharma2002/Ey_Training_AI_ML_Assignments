# ─────────────────────────────────────────────────────────────
# api.py  ·  FastAPI backend
#
# The "external service" the agent queries — it does not own
# this, it just calls it like any third-party API.
#
# Base    GET /orders/{id}     order details
# Ext 3   GET /customers/{id}  customer details (parallel calls)
#
# Runs in-process via TestClient — no server needed.
# To deploy for real, swap the last line:
#   import httpx, os
#   http = httpx.Client(base_url=os.environ["ORDER_API_URL"])
# ─────────────────────────────────────────────────────────────

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

app = FastAPI()

_ORDERS = {
    "A1001": {"id": "A1001", "item": "Mechanical keyboard", "qty": 1, "status": "shipped",    "total": 129.0, "customer_id": "C01"},
    "A1002": {"id": "A1002", "item": "USB-C hub",           "qty": 2, "status": "processing", "total": 58.0,  "customer_id": "C02"},
    "A1003": {"id": "A1003", "item": "4K monitor",          "qty": 1, "status": "delivered",  "total": 410.0, "customer_id": "C01"},
}

_CUSTOMERS = {
    "C01": {"id": "C01", "name": "Asha Sharma", "tier": "gold"},
    "C02": {"id": "C02", "name": "Rohan Mehta",  "tier": "silver"},
}


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    o = _ORDERS.get(order_id.upper())
    if not o:
        raise HTTPException(404, "order not found")
    return o


@app.get("/customers/{customer_id}")          # Extension 3
def get_customer(customer_id: str):
    c = _CUSTOMERS.get(customer_id.upper())
    if not c:
        raise HTTPException(404, "customer not found")
    return c


http = TestClient(app)                        # in-process HTTP client
