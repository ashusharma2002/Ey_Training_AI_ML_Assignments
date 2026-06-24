# Architecture — Observability & Guardrails Toolkit

## System Overview

The notebook builds a **layered observability stack** around a three-agent LLM pipeline. Each layer is added incrementally so you can see exactly what it contributes before the next one is stacked on top.

```
                    ┌─────────────────────────────────────────┐
                    │           INPUT (lead dict)              │
                    └──────────────────┬──────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────┐
                    │         INPUT GUARDRAILS (§5)            │
                    │  • required-field schema check           │
                    │  • prompt-injection heuristic            │
                    │  • topic scope check                     │
                    └──────────────────┬──────────────────────┘
                          blocked ◄────┤──── allowed
                                       │
              ┌────────────────────────▼────────────────────────────┐
              │                  TRACE (§3)                          │
              │   ┌─────────────────────────────────────────────┐   │
              │   │  SPAN: agent.researcher                      │   │
              │   │   └─ SPAN: llm.call  (§4 telemetry)         │   │
              │   └─────────────────────────────────────────────┘   │
              │   ┌─────────────────────────────────────────────┐   │
              │   │  SPAN: agent.summariser                      │   │
              │   │   ├─ SPAN: llm.call                          │   │
              │   │   └─ grounding guardrail check               │   │
              │   └─────────────────────────────────────────────┘   │
              │   ┌─────────────────────────────────────────────┐   │
              │   │  SPAN: agent.notifier                        │   │
              │   │   ├─ SPAN: llm.call                          │   │
              │   │   └─ PII redaction (§6)                      │   │
              │   └─────────────────────────────────────────────┘   │
              └────────────────────────┬────────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────┐
                    │       AUDIT RECORD (§7, Ext. Task 6)     │
                    │  hash(redacted_prompt) + hash(response)  │
                    │  + prev_hash → append-only chain         │
                    │  persisted to audit_log.jsonl on disk    │
                    └──────────────────┬──────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────┐
                    │      QUALITY SCORING (§8, §14)           │
                    │  • lexical groundedness (free)           │
                    │  • LLM groundedness (focused prompt)     │
                    │  • LLM usefulness  (focused prompt)      │
                    │  → QualityReport dataclass               │
                    └──────────────────┬──────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────┐
                    │       DASHBOARD (§10, §15)               │
                    │  cost · latency · retries · blocks       │
                    │  groundedness · usefulness · pass rate   │
                    │  audit chain status                      │
                    └─────────────────────────────────────────┘
```

---

## Layer Details

### 1. `call_claude()` — The Central Chokepoint

Every model call routes through a single function. This is the most important architectural decision: it gives you one place to attach telemetry, guardrails, retries, and logging.

```python
LLMResult(text, model, input_tokens, output_tokens, stop_reason, latency_ms, cost_usd, mock)
```

All downstream layers consume `LLMResult`, never a bare string.

---

### 2. Structured Logging (`LOG_BUFFER`)

Events are emitted as JSON objects with a stable schema:

```json
{"ts": "...", "level": "INFO", "event": "llm.call", "model": "...", "cost_usd": 0.0}
```

In production: stdout → log shipper (Fluentd / Vector) → store (S3 / BigQuery).

---

### 3. Tracing (`SPANS`)

A `Span` has: `name`, `trace_id`, `span_id`, `parent_id`, `start_ms`, `end_ms`, `attributes`, `status`.

The `span()` context manager uses thread-local state (`_CURRENT`) so nested spans automatically form a parent–child tree matching the call stack — the same model OpenTelemetry uses.

---

### 4. LLM Call Telemetry (`LLM_CALLS`)

`instrumented_call()` wraps `call_claude()` inside a span and appends to `LLM_CALLS`. This gives a flat ledger of every model call with cost, latency, and token counts — the input to the cost/latency section of the dashboard.

---

### 5. Input Guardrails

Three checks run before any token hits the model:

| Check | Method | What it catches |
|-------|--------|----------------|
| Schema | `gr_required_fields` | Missing `lead_id`, `company`, `industry` |
| Injection | `gr_prompt_injection` | "ignore previous instructions", "email everyone", etc. |
| Scope | `gr_topic_scope` | Text with no sales-domain terms (warn-only) |

A blocked lead is logged, audited, and returned early — the agents never see it.

---

### 6. Output Guardrails + PII Redaction

`redact(text)` returns `(redacted_text, reidentification_map)`. The map (keyed `<EMAIL_1>`, `<PHONE_1>`, …) is the only place raw PII survives. All logs, audit records, and outreach text use the redacted form.

---

### 7. Hash-Chained Audit Log

Each record stores:
- `prompt_hash` — SHA-256 of the *redacted* prompt
- `response_hash` — SHA-256 of the *redacted* response
- `prev_hash` — hash of the previous record (forms the chain)
- `record_hash` — SHA-256 of all the above fields (seals this record)

Tampering with any field breaks `record_hash`. Tampering with `record_hash` breaks the next record's `prev_hash`. Either way `verify_chain()` returns `False`.

**Extension Task 6** persists this to `audit_log.jsonl` and re-verifies the chain on reload.

---

### 8. Rate Limiting — Token Bucket (Extension Task 3)

The token-bucket algorithm:

```
bucket starts full (capacity = 10 tokens)
each API call consumes 1 token
tokens refill at refill_rate per second
if bucket is empty → block (up to 30 s) before the call goes out
```

This prevents burst traffic from hitting the API hard enough to trigger a 429, without adding unnecessary latency to steady-state traffic.

---

### 9. Groundedness & Usefulness Scoring (Section 14)

Two dimensions, three methods:

```
groundedness_lexical  ─── cheap, deterministic, no API
groundedness_llm      ─┬─ focused prompt: "is every claim supported?"
usefulness_llm        ─┘─ focused prompt: "is this actionable for sales?"

QualityReport.passed = (lex ≥ 0.25) AND (gnd_llm ≥ 3) AND (use_llm ≥ 3)
```

Keeping groundedness and usefulness in separate prompts avoids the "trade-off bias" where a combined prompt averages two bad scores into one mediocre one.
