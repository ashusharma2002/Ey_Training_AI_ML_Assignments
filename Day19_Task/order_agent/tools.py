# ─────────────────────────────────────────────────────────────
# tools.py  ·  Tool schemas + implementations + dispatch
#
# Claude reads the JSON schemas to decide which tool to call.
# Your Python functions run when it does.
#
# Tools
# ─────────────────────────────────────────────────────────────
# get_order      GET /orders/{id}         base
# get_customer   GET /customers/{id}      Ext 3  parallel calls
# remember_fact  Redis HASH set           base + Ext 2 + Ext 4
# recall_fact    Redis HASH get           base
# forget_fact    Redis HASH del           Ext 2
#
# Extensions implemented here
# ─────────────────────────────────────────────────────────────
# Ext 2  forget_fact tool
# Ext 3  get_customer tool  →  Claude emits two tool_use blocks
#        in a single response (parallel)
# Ext 4  PII guard on remember_fact  →  rejects card numbers,
#        emails, and phone numbers before writing to Redis
# ─────────────────────────────────────────────────────────────

import re
from api    import http
from memory import RedisMemory


# ── JSON schemas (what Claude reads) ──────────────────────────

TOOLS = [
    {
        "name": "get_order",
        "description": "Look up an order by ID. Returns item, qty, status, total, customer_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID, e.g. 'A1001'.",
                    "pattern": "^[Aa][0-9]{4}$",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_customer",                        # Extension 3
        "description": "Look up a customer by customer_id. Returns name and membership tier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID, e.g. 'C01'."}
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "remember_fact",
        "description": (
            "Persist a user preference for future turns "
            "(e.g. shipping_pref, budget). "
            "Never store card numbers, emails, or phone numbers."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key":   {"type": "string", "description": "Short key, e.g. 'shipping_pref'."},
                "value": {"type": "string", "description": "Value to store."},
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "recall_fact",
        "description": "Retrieve a stored user preference by key.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key to look up."}
            },
            "required": ["key"],
        },
    },
    {
        "name": "forget_fact",                         # Extension 2
        "description": "Permanently delete a stored user preference by key.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key to delete."}
            },
            "required": ["key"],
        },
    },
]


# ── Extension 4: PII guard ─────────────────────────────────────

_CARD  = re.compile(r"(\d[ \-]?){13,19}")
_EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE = re.compile(r"(\+?91[\-\s]?)?[6-9]\d{9}|(\+?1[\-\s]?)?\(?\d{3}\)?[\-\s]?\d{3}[\-\s]?\d{4}")

def _is_pii(value: str) -> tuple[bool, str | None]:
    v = value.replace(" ", "").replace("-", "")
    if _CARD.search(v):  return True, "Looks like a card number — cannot store that."
    if _EMAIL.search(value): return True, "Looks like an email — cannot store that."
    if _PHONE.search(v): return True, "Looks like a phone number — cannot store that."
    return False, None


# ── Tool implementations ───────────────────────────────────────
# Errors are RETURNED (not raised) so the loop can send
# is_error=True and Claude can recover gracefully.

def _get_order(order_id: str) -> dict:
    r = http.get(f"/orders/{order_id}")
    return r.json() if r.status_code == 200 else {"error": f"Order {order_id} not found."}

def _get_customer(customer_id: str) -> dict:           # Extension 3
    r = http.get(f"/customers/{customer_id}")
    return r.json() if r.status_code == 200 else {"error": f"Customer {customer_id} not found."}

def _remember(mem: RedisMemory, key: str, value: str) -> dict:
    pii, reason = _is_pii(value)                       # Extension 4
    if pii:
        return {"error": reason}
    mem.set_fact(key, value)
    return {"ok": True, "stored": {key: value}}

def _recall(mem: RedisMemory, key: str) -> dict:
    return {"key": key, "value": mem.get_fact(key)}

def _forget(mem: RedisMemory, key: str) -> dict:       # Extension 2
    mem.forget_fact(key)
    return {"ok": True, "deleted": key}


# ── Dispatch ───────────────────────────────────────────────────

def make_dispatch(mem: RedisMemory) -> dict:
    return {
        "get_order":     lambda order_id: _get_order(order_id),
        "get_customer":  lambda customer_id: _get_customer(customer_id),
        "remember_fact": lambda key, value: _remember(mem, key, value),
        "recall_fact":   lambda key: _recall(mem, key),
        "forget_fact":   lambda key: _forget(mem, key),
    }


def run_tool(dispatch: dict, name: str, args: dict) -> tuple[dict, bool]:
    fn = dispatch.get(name)
    if not fn:
        return {"error": f"unknown tool: {name}"}, True
    try:
        out = fn(**args)
        return out, ("error" in out if isinstance(out, dict) else False)
    except Exception as e:
        return {"error": repr(e)}, True
