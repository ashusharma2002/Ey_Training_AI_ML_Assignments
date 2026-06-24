# Pipeline Diagram

## Naive Pipeline (Before Instrumentation)

```
Lead dict
   │
   ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Researcher  │────▶│  Summariser  │────▶│   Notifier   │
│  (enrich)    │     │  (condense)  │     │  (outreach)  │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
                                          outreach string
```

No visibility into cost, latency, errors, PII, or quality.

---

## Instrumented Pipeline (After All Layers)

```
Lead dict
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│  INPUT GUARDRAILS                                               │
│  ① required-field schema check                                  │
│  ② prompt-injection heuristic  (catches "ignore instructions")  │
│  ③ topic scope check                                            │
└───────────────────────────────┬─────────────────────────────────┘
               BLOCKED ◄────────┤────────► ALLOWED
                                │
                       log_event("guardrail.block")
                       audit(..., decision="block")
                       return early
                                │
   ┌────────────────────────────▼────────────────────────────────┐
   │  TRACE  (trace_id bound for this request)                    │
   │                                                              │
   │  ┌─ SPAN: agent.researcher ──────────────────────────────┐  │
   │  │   ┌─ SPAN: llm.call ────────────────────────────────┐ │  │
   │  │   │  model=haiku | tokens | latency | cost          │ │  │
   │  │   └────────────────────────────────────────────────┘ │  │
   │  │   audit(actor, "researcher", prompt_hash, resp_hash)  │  │
   │  └───────────────────────────────────────────────────────┘  │
   │                                                              │
   │  ┌─ SPAN: agent.summariser ──────────────────────────────┐  │
   │  │   ┌─ SPAN: llm.call ────────────────────────────────┐ │  │
   │  │   │  model=sonnet | tokens | latency | cost         │ │  │
   │  │   └────────────────────────────────────────────────┘ │  │
   │  │   gr_grounded(summary, source)  ← output guardrail   │  │
   │  │   audit(actor, "summariser", ...)                     │  │
   │  └───────────────────────────────────────────────────────┘  │
   │                                                              │
   │  ┌─ SPAN: agent.notifier ───────────────────────────────┐   │
   │  │   ┌─ SPAN: llm.call ────────────────────────────────┐│   │
   │  │   │  model=haiku | tokens | latency | cost          ││   │
   │  │   └────────────────────────────────────────────────┘│   │
   │  │   redact(output)  ← PII guardrail                    │   │
   │  │   audit(actor, "notifier", redacted_text, ...)       │   │
   │  └───────────────────────────────────────────────────────┘  │
   └────────────────────────────┬────────────────────────────────┘
                                │
                                ▼
                  ┌─────────────────────────┐
                  │  QUALITY SCORING         │
                  │  lexical groundedness    │
                  │  LLM groundedness        │
                  │  LLM usefulness          │
                  │  → QualityReport         │
                  └─────────────┬───────────┘
                                │
                                ▼
                  ┌─────────────────────────┐
                  │  AUDIT LOG (§7 + Ext.6) │
                  │  hash-chained .jsonl    │
                  │  persisted to disk      │
                  └─────────────────────────┘
                                │
                                ▼
                  ┌─────────────────────────┐
                  │  DASHBOARD (§10 + §15)   │
                  │  cost · tokens · latency │
                  │  blocks · retries        │
                  │  groundedness · quality  │
                  │  chain integrity         │
                  └─────────────────────────┘
```

---

## Rate Limiting Layer (Extension Task 3)

Wraps every `call_claude()` invocation:

```
call_claude_with_retries()
         │
         ▼
   ┌─────────────┐     empty?    ┌──────────────────────────┐
   │ Token Bucket│─────────────▶│ block (poll every 50 ms) │
   │  capacity=10│              │ up to 30 s timeout        │
   │  refill=5/s │              └──────────────────────────┘
   └──────┬──────┘
    granted │
         ▼
   ┌─────────────┐   exception?  ┌──────────────────────────┐
   │  call_claude│─────────────▶│ exponential backoff       │
   │  (live/mock)│              │ base × 2^attempt + jitter │
   └──────┬──────┘              │ retry up to max_retries   │
    ok    │                     └──────────────────────────┘
         ▼
   LLMResult + span attributes
   { retry_count, rate_limited }
```
