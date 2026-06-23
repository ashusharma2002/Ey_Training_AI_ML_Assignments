# ─────────────────────────────────────────────────────────────
# agent.py  ·  The Claude agent loop
#
# This is the heart of the project.
# The loop is driven entirely by stop_reason — no step counting.
#
# Flow
#   1. append user message → load history → call Claude
#   2. stop_reason == "tool_use"
#        run every tool_use block → send tool_results → loop
#   3. stop_reason == "end_turn"
#        save reply to Redis → return text
#
# Extensions wired in here
# ─────────────────────────────────────────────────────────────
# Ext 1  compact_if_needed() called before every API request
# Ext 5  resp.usage tracked each step; totals printed at end
# ─────────────────────────────────────────────────────────────

import json, os
from dotenv import load_dotenv

load_dotenv()

from anthropic import Anthropic
from memory import RedisMemory, compact_if_needed
from tools  import TOOLS, make_dispatch, run_tool

MODEL    = "claude-sonnet-4-6"
MAX_STEPS = 10
SYSTEM = (
    "You are an order-support assistant. "
    "Use get_order for order questions. "
    "Use get_customer to fetch customer details by customer_id. "
    "Use remember_fact / recall_fact for user preferences. "
    "Use forget_fact when the user wants to remove a preference. "
    "Never store card numbers, emails, or phone numbers. "
    "Be concise."
)


class Agent:

    def __init__(self, session_id: str = "default"):
        self.mem      = RedisMemory(session_id)
        self.dispatch = make_dispatch(self.mem)
        self.live     = bool(os.environ.get("ANTHROPIC_API_KEY"))
        self._claude  = Anthropic() if self.live else None

    def chat(self, user_text: str, verbose: bool = True) -> str:
        self.mem.append_turn("user", user_text)

        if not self.live:
            return self._mock(user_text)

        messages    = compact_if_needed(self.mem, self._claude)   # Ext 1
        total_in    = 0
        total_out   = 0

        for step in range(MAX_STEPS):
            resp = self._claude.messages.create(
                model=MODEL, max_tokens=1024,
                system=SYSTEM, tools=TOOLS, messages=messages,
            )

            total_in  += resp.usage.input_tokens    # Ext 5
            total_out += resp.usage.output_tokens   # Ext 5

            if resp.stop_reason == "tool_use":
                messages.append({
                    "role": "assistant",
                    "content": [b.model_dump() for b in resp.content],
                })
                results = []
                for b in resp.content:
                    if b.type == "tool_use":
                        if verbose:
                            print(f"  → {b.name}({b.input})")
                        out, is_err = run_tool(self.dispatch, b.name, b.input)
                        results.append({
                            "type":        "tool_result",
                            "tool_use_id": b.id,
                            "content":     json.dumps(out),
                            "is_error":    is_err,
                        })
                messages.append({"role": "user", "content": results})
                continue

            # end_turn
            reply = "".join(b.text for b in resp.content if b.type == "text")
            self.mem.append_turn("assistant", reply)
            if verbose:
                print(f"  ✓ {step+1} step(s)  |  tokens: in={total_in} out={total_out} total={total_in+total_out}")
            return reply

        return "(max steps reached)"

    def reset(self):
        self.mem.clear_history()

    def _mock(self, text: str) -> str:
        import re
        m = re.search(r"A\d{4}", text.upper())
        if m:
            from tools import _get_order
            o     = _get_order(m.group())
            reply = f"(mock) {m.group()}: status={o.get('status','?')}, total=${o.get('total','?')}"
        else:
            reply = "(mock) Try asking about orders A1001–A1003."
        self.mem.append_turn("assistant", reply)
        return reply
