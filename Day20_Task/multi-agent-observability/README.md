# Observability for a Multi-Agent System

A coding assignment solution that upgrades a bare-bones progress listener into a fully correlated, structured observability layer for a simulated multi-agent pipeline.

**No external packages. Runs offline. Python 3.9+ only.**

---

## What this does

A client runs an agentic pipeline: **Planner → Researcher → Writer → Reviewer**.  
The original code only printed raw lines like `Researcher: step 3/6` — useless for debugging overnight failures.

This solution replaces that with structured JSON telemetry that an ops team can actually use.

---

## Quick start

```bash
python agents.py                        # run the pipeline
python agents.py | python -m json.tool  # pretty-print each event
python agents.py > trace.jsonl          # persist to a JSONL file
```

To test the **failure path**, open `agents.py` and change:
```python
Agent("Writer", 4)  →  Agent("Writer", 4, fail_at_step=2)
```

---

## Events emitted

Every event carries: `timestamp`, `trace_id`, `span_id`, `event`, `agent`.

| Event | Fired when | Key extra fields |
|---|---|---|
| `agent_started` | Before an agent begins | `total_steps`, `pipeline_pct_complete` |
| `agent_progress` | Every ~25% of an agent's steps | `step`, `agent_pct_complete`, `pipeline_pct_complete`, `throughput_steps_per_s` |
| `agent_completed` | Agent finishes successfully | `duration_s`, `throughput_steps_per_s` |
| `agent_failed` | Agent raises `RuntimeError` | `failed_at_step`, `error`, `pipeline_pct_complete` |
| `run_summary` | Always last (success or failure) | `status`, `total_duration_s`, `agents_completed`, `failed_agent`, `failed_at_step` |

---

## Correlation model

```
Run
└── trace_id  (one UUID per Orchestrator.run() call)
    ├── Planner   span_id  (one UUID per agent execution)
    ├── Researcher span_id
    ├── Writer    span_id
    └── Reviewer  span_id
```

- **`trace_id`** is identical on every event in a run — use it to group all events from one run.
- **`span_id`** is unique per agent — use it to isolate one agent's events within a run.

This is a simplified version of OpenTelemetry spans and maps directly onto AWS X-Ray traces/segments.

---

## Sample output (success)

```json
{"timestamp": "2026-06-24T09:14:02.123Z", "trace_id": "5f2c3a1b-...", "span_id": "a91b4c2d-...", "event": "agent_started",   "agent": "Planner",    "total_steps": 3,  "pipeline_pct_complete": 0.0}
{"timestamp": "2026-06-24T09:14:02.298Z", "trace_id": "5f2c3a1b-...", "span_id": "a91b4c2d-...", "event": "agent_progress",  "agent": "Planner",    "step": 1, "total_steps": 3, "agent_pct_complete": 33.3, "pipeline_pct_complete": 6.7,  "throughput_steps_per_s": 5.4}
{"timestamp": "2026-06-24T09:14:02.441Z", "trace_id": "5f2c3a1b-...", "span_id": "a91b4c2d-...", "event": "agent_completed", "agent": "Planner",    "duration_s": 0.318, "pipeline_pct_complete": 20.0, "throughput_steps_per_s": 9.4}
...
{"timestamp": "2026-06-24T09:14:04.010Z", "trace_id": "5f2c3a1b-...",                             "event": "run_summary",    "status": "success",   "total_duration_s": 1.887, "agents_completed": ["Planner","Researcher","Writer","Reviewer"], "failed_agent": null, "pipeline_pct_complete": 100.0}
```

## Sample output (failure — Writer fails at step 2)

```json
{"timestamp": "...", "trace_id": "5f2c3a1b-...", "span_id": "7bb0f81b-...", "event": "agent_failed",  "agent": "Writer", "failed_at_step": 2, "error": "Writer failed at step 2", "pipeline_pct_complete": 66.7}
{"timestamp": "...", "trace_id": "5f2c3a1b-...",                             "event": "run_summary",   "status": "failed", "total_duration_s": 1.321, "agents_completed": ["Planner","Researcher"], "failed_agent": "Writer", "failed_at_step": 2, "pipeline_pct_complete": 66.7}
```

---

## Acceptance criteria

| # | Requirement | Status |
|---|---|---|
| 1 | Emit structured JSON events, not free-text prints | ✅ |
| 2 | Correlate via run-level `trace_id` and per-agent `span_id` | ✅ |
| 3 | Report pipeline % complete, throughput, and per-agent duration | ✅ |
| 4 | Throttle progress events (not one per step) | ✅ |
| 5 | Failure event localizes which agent/step broke + run summary | ✅ |
| 6 | Runs with `python agents.py` — no pip installs | ✅ |

---

## Submission note

**Next signal to capture for a real agentic workload:** `token_count` and `estimated_cost_usd` per `agent_completed` — in a real LLM pipeline, runaway token usage is the most expensive silent failure and "step X/Y" tells you nothing about it.

**Where these events would go in a client environment:**  
1. **AWS CloudWatch Logs Insights** — each JSON event becomes a structured log entry; queryable across runs (e.g. *"all runs where Researcher took > 30 s"*).  
2. **AWS X-Ray / Honeycomb** — `trace_id` maps to a trace, `span_id` maps to a segment/span, giving the ops team a waterfall diagram of agent handoffs to pinpoint bottlenecks instantly.

---

## Files

```
agents.py   — complete solution (single file, Python stdlib only)
README.md   — this file
```
