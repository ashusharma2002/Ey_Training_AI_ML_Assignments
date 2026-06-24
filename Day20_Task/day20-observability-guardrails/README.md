# Day 20 · Observability & Guardrails Toolkit
### Production Multi-Agent Systems — Anthropic API Course

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/jupyter-notebook-orange)](https://jupyter.org/)
[![Anthropic](https://img.shields.io/badge/Anthropic-Claude%20API-blueviolet)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## Overview

This project wraps a naive three-agent LLM pipeline (**Researcher → Summariser → Notifier**) with production-grade observability and safety layers, built step-by-step from scratch using the Anthropic Claude API.

The extended notebook completes **Extension Tasks 3 & 6** from the original course material and adds a richer **Groundedness & Usefulness** evaluation framework.

---

## Project Structure

```
day20-observability-guardrails/
│
├── README.md                          ← You are here
├── LICENSE
├── .gitignore
├── requirements.txt                   ← Python dependencies
│
├── notebooks/
│   ├── Day20_Colab1_Observability_Guardrails_Original.ipynb   ← Original course notebook
│   └── Day20_Colab1_Observability_Guardrails_Extended.ipynb   ← Extended notebook (this work)
│
├── docs/
│   ├── ARCHITECTURE.md                ← System design & layer descriptions
│   ├── EXTENSION_TASKS.md             ← Detailed write-up of ext. tasks 3 & 6
│   └── GROUNDEDNESS_USEFULNESS.md     ← Scoring methodology deep-dive
│
└── assets/
    └── pipeline_diagram.md            ← ASCII pipeline diagram
```

---

## What the Notebook Builds

The notebook layers observability and safety onto a three-agent pipeline one piece at a time:

| Section | Layer | What It Does |
|---------|-------|-------------|
| 0 | Setup | `call_claude()` wrapper + mock mode (runs without an API key) |
| 1 | Naive pipeline | The "before" — functional but a complete black box |
| 2 | Structured logging | Every event as a JSON object with stable schema |
| 3 | Tracing | `Trace`/`Span` tree (OpenTelemetry-compatible model) |
| 4 | LLM telemetry | Tokens, latency, cost, `stop_reason` per call |
| 5 | Input guardrails | Schema checks, prompt-injection detection, topic scope |
| 6 | Output guardrails | PII detection & redaction, typed token replacement |
| 7 | Audit log | Append-only, hash-chained tamper-evident record |
| 8 | Feedback loop | LLM-as-judge scoring + metric aggregation |
| 9 | Full pipeline | All layers wired together end-to-end |
| 10 | Dashboard | Reads all telemetry back out into a unified view |
| **12** | **Ext. Task 3** | **Token-bucket rate limiting + exponential-backoff retries** |
| **13** | **Ext. Task 6** | **Persist audit log to disk (JSON Lines) + chain re-verification** |
| **14** | **Enhanced scoring** | **Separate LLM probes for groundedness & usefulness** |
| **15** | **Extended dashboard** | **All extension metrics in one view** |

---

## Extension Tasks Completed

### ✅ Extension Task 3 — Token-Bucket Rate Limiting & Retries

Adds two safety nets around every `call_claude()` invocation:

- **`TokenBucket`** — thread-safe, configurable capacity (default: 10 req burst, 5 req/s refill). Blocks callers until capacity is available rather than letting them crash into a 429.
- **`call_claude_with_retries()`** — exponential backoff (`base × 2ᵃᵗᵗᵉᵐᵖᵗ + jitter`) with up to 3 retries before raising `MaxRetriesExceeded`.
- `retry_count` and `rate_limited` are stamped onto every span so the dashboard surfaces throttling trends.

### ✅ Extension Task 6 — Persistent Audit Log

Makes the hash-chained audit log durable across restarts:

- **`persist_audit_log()`** — writes to `audit_log.jsonl` (JSON Lines) in append-only or overwrite mode; deduplicates on `record_hash` so re-runs are idempotent.
- **`verify_chain_from_disk()`** — reloads and re-verifies the entire hash chain, returning the exact index of any tampered record.
- Tampering simulation included: editing one record's field is immediately detected.

### ✅ Enhanced Groundedness & Usefulness Scoring

Replaces the single combined judge prompt with three separate scoring methods:

| Method | Cost | What it measures |
|--------|------|-----------------|
| `score_groundedness_lexical` | Free | Token-overlap ratio between summary and source |
| `score_groundedness_llm` | 1 API call | Factual faithfulness (1–5) with chain-of-thought |
| `score_usefulness_llm` | 1 API call | Sales-rep actionability (1–5) with chain-of-thought |

A `QualityReport` dataclass reconciles all three into normalised 0–1 scores and a `passed` boolean.

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/day20-observability-guardrails.git
cd day20-observability-guardrails
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

> Without a key, the notebook runs in **mock mode** — all model calls return canned responses. Every cell still executes end-to-end.

### 4. Open the notebook

```bash
jupyter notebook notebooks/Day20_Colab1_Observability_Guardrails_Extended.ipynb
```

Or open in **Google Colab**:

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<your-username>/day20-observability-guardrails/blob/main/notebooks/Day20_Colab1_Observability_Guardrails_Extended.ipynb)

### 5. Run all cells top to bottom

`Runtime → Run all` (Colab) or `Kernel → Restart & Run All` (Jupyter).

---

## Requirements

See `requirements.txt` for pinned versions. Core dependencies:

```
anthropic>=0.25.0
jupyter>=1.0.0
```

Everything else (`re`, `hashlib`, `uuid`, `threading`, `json`, `dataclasses`, `pathlib`) is Python standard library — no extra installs needed.

---

## Mock Mode vs Live Mode

| | Mock mode (`USE_MOCK=True`) | Live mode |
|--|--|--|
| API key required | ❌ | ✅ |
| Network calls | None | Anthropic API |
| Reproducible | ✅ | ❌ (LLM non-determinism) |
| Cost | $0 | ~$0.001 per full pipeline run |
| Use case | Learning / CI | Production testing |

Mock mode is the default. Set `ANTHROPIC_API_KEY` in your environment and `USE_MOCK` flips to `False` automatically.

---

## Key Concepts Demonstrated

- **Structured logging** — machine-readable JSON events vs. `print()`
- **Distributed tracing** — parent/child span trees, same model as OpenTelemetry
- **LLM telemetry** — per-call cost, latency, token counts, `stop_reason`
- **Input guardrails** — schema validation, prompt-injection heuristics
- **Output guardrails** — PII redaction with typed tokens and sealed re-id map
- **Hash-chained audit logs** — tamper-evident governance records
- **LLM-as-judge** — automated quality scoring with grounded, explainable output
- **Rate limiting** — token-bucket algorithm with exponential-backoff retries
- **Persistent storage** — JSON Lines append-only log with cross-session chain verification

---

## File Descriptions

| File | Purpose |
|------|---------|
| `notebooks/Day20_Colab1_Observability_Guardrails_Extended.ipynb` | **Main deliverable** — original course notebook + all extensions |
| `notebooks/Day20_Colab1_Observability_Guardrails_Original.ipynb` | Original course notebook (unchanged, for reference/diff) |
| `docs/ARCHITECTURE.md` | Layer-by-layer system design notes |
| `docs/EXTENSION_TASKS.md` | Detailed write-up of what each extension task implements |
| `docs/GROUNDEDNESS_USEFULNESS.md` | Deep-dive on the scoring methodology |
| `requirements.txt` | Pinned Python dependencies |

---

## Course Context

This notebook is **Day 20, Colab 1** of the Anthropic API production course.

- **Day 20 theme:** Production multi-agent systems — observability, guardrails, auditing
- **Colab 1 goal:** Build the observability machinery layer by layer
- **Colab 2** (not in this repo): Full capstone — four agents, compliance gate, working feedback loop

---

## License

MIT — see [LICENSE](LICENSE).
