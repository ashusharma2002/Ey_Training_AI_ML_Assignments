# Groundedness & Usefulness — Scoring Methodology

## Why Separate Scoring Dimensions

The original `judge_output` function combined both scores into one prompt:

```python
"Rate this lead summary for groundedness and usefulness (1-5 each). Return JSON only."
```

This works but has a **trade-off bias problem**: when you ask a single LLM call to evaluate two correlated but independent dimensions, it tends to average its overall impression. A summary that is highly grounded but completely useless ends up with mediocre scores on both — not a 5 on groundedness and a 1 on usefulness.

The solution is **separate, focused prompts** — one per dimension.

---

## The Three Methods

### Method 1: Lexical Groundedness (Free, Deterministic)

```python
def score_groundedness_lexical(summary: str, source: str, min_word_len: int = 4) -> float:
```

**How it works:**  
Extract all words of ≥ 4 characters from both summary and source (filters out stop words like "the", "and", "that"). Compute the fraction of summary words that also appear in the source.

```
score = |summary_words ∩ source_words| / |summary_words|
```

**Thresholds:**
- ≥ 0.40 → strongly grounded
- 0.25–0.40 → acceptable (paraphrasing is normal)
- < 0.25 → suspicious; flag for LLM review

**Limitations:**
- Cannot handle paraphrasing or synonyms ("logistics" vs "supply chain")
- Does not understand negation ("not struggling" ≠ "struggling")
- Low scores should trigger LLM review, not automatic rejection

**Why use it?** It catches blatant hallucinations (invented proper nouns, fabricated statistics) cheaply — no API call, perfectly reproducible, runs in microseconds.

---

### Method 2: LLM-Graded Groundedness

**System prompt:**
> "You are a strict factual-accuracy judge. Your job is to decide whether a summary contains ONLY information that can be directly traced back to the source text."

**Scale:**

| Score | Meaning |
|-------|---------|
| 5 | Every claim in the summary is supported by the source |
| 4 | Nearly all claims are supported; minor inference acceptable |
| 3 | Most claims supported but one or two go beyond the source |
| 2 | Several claims are not supported or are distorted |
| 1 | The summary is largely hallucinated or contradicts the source |

**JSON output schema:**
```json
{
  "groundedness": 4,
  "unsupported_claims": ["none"],
  "notes": "One-sentence explanation"
}
```

The `unsupported_claims` field is key — it makes the score **explainable**, not just a number.

---

### Method 3: LLM-Graded Usefulness

**System prompt:**
> "You are a sales-enablement quality coach. Your job is to judge whether a lead summary gives a sales rep everything they need to take immediate, tailored action."

**Scale:**

| Score | Meaning |
|-------|---------|
| 5 | Contains clear pain, decision-making context, size/budget signals, and a specific suggested next step |
| 4 | Contains most of the above; one dimension slightly thin |
| 3 | Gives some relevant context but a rep would still need to do research |
| 2 | Vague or generic; does not meaningfully guide outreach |
| 1 | Useless or misleading for sales purposes |

**JSON output schema:**
```json
{
  "usefulness": 3,
  "missing_elements": ["budget signal", "next step"],
  "notes": "One-sentence explanation"
}
```

---

## The `QualityReport` Dataclass

```python
@dataclass
class QualityReport:
    groundedness_lexical: float   # 0.0 – 1.0  token-overlap ratio
    groundedness_llm:     int     # 1 – 5       LLM-graded faithfulness
    groundedness_notes:   str     # LLM chain-of-thought
    usefulness_llm:       int     # 1 – 5       LLM-graded actionability
    usefulness_notes:     str     # LLM chain-of-thought
    groundedness_final:   float   # reconciled 0 – 1
    usefulness_final:     float   # normalised 0 – 1
    passed:               bool    # True if all thresholds met
```

### Reconciliation Logic

```python
if lex < 0.25 AND gnd_llm < 3:
    # Both methods agree something is wrong → blend for a penalty
    groundedness_final = (lex + (gnd_llm - 1) / 4) / 2
else:
    # Trust the LLM (it handles paraphrase; lexical can't)
    groundedness_final = (gnd_llm - 1) / 4   # normalise 1-5 → 0-1
```

The **OR rule** for `passed` is intentionally strict — a summary must pass all three checks:

```python
passed = (lex >= 0.25) AND (gnd_llm >= 3) AND (use_llm >= 3)
```

---

## Test Results

Three test cases were designed to validate independence of the two dimensions:

| Test Case | Lex. Overlap | Gnd. LLM | Use. LLM | Passed |
|-----------|-------------|---------|---------|--------|
| Good (grounded + useful) | high | 4–5 | 4–5 | ✅ |
| Hallucinated (invented claims) | low | 1–2 | 3–4 | ❌ |
| Vague (accurate but useless) | moderate | 4 | 1–2 | ❌ |

Key observation: the **vague test case** scores well on groundedness (it says little, so little is wrong) but poorly on usefulness — this is exactly the independence the separate-prompt design was intended to produce.

---

## Dashboard Metrics

The extended dashboard reports:

```
avg groundedness (lex) : 0.412   (token overlap, 0–1)
avg groundedness (llm) : 3.3/5
avg usefulness   (llm) : 2.7/5
quality pass rate      : 33%
```

These metrics feed directly into the feedback loop described in Section 8 — low pass rates signal that prompts, agent instructions, or model tier choices need tuning.
