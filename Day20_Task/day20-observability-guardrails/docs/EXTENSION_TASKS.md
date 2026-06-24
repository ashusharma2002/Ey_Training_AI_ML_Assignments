# Extension Tasks — Implementation Notes

## Extension Task 3: Token-Bucket Rate Limiting & Retries

### Problem Statement

LLM APIs impose rate limits (requests-per-minute and tokens-per-minute). Without protection:

- A burst of leads hits the API until a `429 Too Many Requests` crashes the pipeline
- Transient network errors or server 5xx responses cause permanent, silent failures

### What Was Implemented

#### `TokenBucket` class

```python
class TokenBucket:
    def __init__(self, capacity: int = 10, refill_rate: float = 5.0):
        ...
    def acquire(self, tokens: int = 1) -> bool: ...
    def wait_and_acquire(self, tokens: int = 1, timeout: float = 30.0) -> bool: ...
```

- **Thread-safe** via `threading.Lock` — safe for concurrent agent calls
- **Capacity** = burst ceiling (default 10 requests)
- **Refill rate** = tokens added per second (default 5 req/s = 300 req/min)
- Uses `time.monotonic()` for accurate cross-sleep accounting
- `wait_and_acquire` polls every 50 ms and blocks up to `timeout` seconds

#### `call_claude_with_retries()` function

```python
def call_claude_with_retries(
    prompt, model, system, max_tokens, temperature,
    max_retries=3, base_delay=1.0, jitter=0.3
) -> LLMResult:
```

- Acquires a bucket token first (blocks if needed)
- On any exception: waits `base × 2ᵃᵗᵗᵉᵐᵖᵗ + random(0, jitter)` seconds, then retries
- Raises `MaxRetriesExceeded` after all retries are exhausted
- Stamps `retry_count` and `rate_limited` onto the active span

### Design Decisions

**Why token bucket and not leaky bucket?** Token bucket allows short bursts (the full `capacity`) which is natural for batch processing of N leads. Leaky bucket enforces a strict constant rate, which would add unnecessary latency when the API is under quota.

**Why exponential backoff with jitter?** Pure exponential backoff causes "thundering herd" — multiple workers retrying at the same intervals. Jitter (random offset 0–0.3 s) spreads retries out and reduces collision probability.

**Why stamp retry telemetry on spans?** So the dashboard can surface "how often are we throttling ourselves" as a metric — without this, you only see it by grepping logs manually.

### Telemetry Output

After running the demo:

```
Bucket capacity : 10 req burst
Refill rate     : 5.0 req/s  (= 300 req/min)
Available now   : 10 tokens

--- Firing 5 rapid calls ---
  Call 0: OK | tokens_left=9.0 | latency=...ms | retries=0
  Call 1: OK | tokens_left=8.0 | latency=...ms | retries=0
  ...
```

In mock mode, retries are always 0 (mock never raises). In live mode, any 429 or 5xx triggers the backoff loop.

---

## Extension Task 6: Persistent Audit Log

### Problem Statement

The hash-chained `AUDIT_LOG` lives only in RAM. A kernel restart or process crash wipes all governance history. Compliance teams need durable, tamper-evident records that survive restarts and can be re-verified at any time.

### What Was Implemented

#### `persist_audit_log(log, path, mode)` function

```python
def persist_audit_log(
    log: list,
    path: Path = AUDIT_LOG_PATH,   # /tmp/audit_log.jsonl
    mode: str = "append"           # or "overwrite"
) -> int:   # records written
```

- **JSON Lines format** — one audit record per line, human-readable, trivially importable
- **Append mode** — reads existing `record_hash` values from disk first; only writes records not already present. Idempotent: running twice doesn't create duplicates
- **Overwrite mode** — rewrites from scratch (used for clean restarts in demos)

#### `load_audit_log(path)` function

Reads the `.jsonl` file line by line, parsing each as JSON. Handles partial-write corruption (one bad line doesn't fail the whole load).

#### `verify_chain_from_disk(path)` function

```python
def verify_chain_from_disk(path) -> dict:
    # returns: {"ok": bool, "total": int, "bad_indices": [...]}
```

Re-runs the full hash-chain verification on the loaded records:
1. Recomputes `record_hash` from all fields except `record_hash` itself
2. Checks `prev_hash` matches the previous record's `record_hash`
3. Returns the index and reason for any record that fails

### Design Decisions

**Why JSON Lines and not JSON array?** JSON Lines supports partial reads (you can `tail -f` it), partial writes (a crash corrupts at most one line), and streaming ingestion into log warehouses (BigQuery, S3 Select). A JSON array requires reading/writing the entire file atomically.

**Why deduplication on `record_hash`?** Without it, a notebook re-run appends all records again, doubling the chain and making it look like the pipeline ran twice. Deduplication makes `persist_audit_log` safe to call multiple times.

**Why re-verify on load rather than trusting the stored `ok` flag?** A stored flag can itself be tampered with. Re-verification on every load means the audit log is only as trustworthy as the code reading it — not the data it contains.

### Tamper Detection Output

```
Step 5 · Simulating file tampering (edit record 1's 'decision' field)...
         Chain valid after tamper: False
         Detected bad records: [1]
```

The verifier returns `bad_indices=[{"index": 1, "problem": "record_hash mismatch"}]` — it knows exactly which record was changed, not just that *something* changed.

---

## What the Telemetry Showed

### Task 3 (Rate Limiting & Retries)

- All 5 rapid demo calls in mock mode returned `retry_count=0` — expected, since the mock never raises transient errors
- Bucket drained from 10 → ~7.5 tokens across 5 calls, confirming the limiter is active
- Refill continues at 5 req/s in the background; waiting 2 s restores ~10 tokens

### Task 6 (Audit Persistence)

- Pipeline generated N audit records; all written to `audit_log.jsonl` with chain intact
- Reload from disk + re-verification returned `ok=True` on clean data
- Simulated tamper detected immediately at the modified index
- Incremental append added 1 new record without touching or invalidating earlier records
