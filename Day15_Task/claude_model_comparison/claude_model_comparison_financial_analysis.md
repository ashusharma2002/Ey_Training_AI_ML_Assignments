# Claude Model Comparison — Financial Analysis

![Models](https://img.shields.io/badge/models-Haiku_·_Sonnet_·_Opus-blue)
![Task](https://img.shields.io/badge/task-Financial_Analysis-green)
![Winner](https://img.shields.io/badge/best_overall-Sonnet_4.6-blueviolet)

Same prompt. Three models. Who does it best?

---

## The Prompt

```
A tech company reports: Revenue up 12% YoY, but gross margins fell from 68% to 61%,
operating expenses rose 31%, and the CFO mentioned 'investment in AI infrastructure.'
The CEO said growth is 'on track.' Is this a healthy quarter? What should an analyst flag?
```

---

## Responses at a Glance

| | Haiku 4.5 | Sonnet 4.6 | Opus 4.6 |
|---|---|---|---|
| **Length** | ~300 words | ~600 words | ~1,100 words |
| **Tone** | Quick triage | Structured analysis | Institutional depth |
| **Did the gross profit math?** | ❌ | ✅ | ✅ |
| **Caught the 2.5% incremental margin?** | ❌ | ❌ | ✅ |
| **Flagged CapEx vs. OpEx accounting issue?** | ❌ | ✅ | ✅ |
| **Challenged management language?** | ⚠️ Surface | ✅ Direct | ✅ With 3 scenarios |
| **Flags tiered by priority?** | ❌ | ✅ 3 tiers | ✅ 4 tiers |
| **Overall score** | 4 / 14 | 10.5 / 14 | 12.5 / 14 |

---

## Model Responses

### 🟢 Haiku 4.5

> Fast. Accurate. Shallow.

**Is this healthy?** No. Revenue growth is positive but the economics underneath are deteriorating.

**Flags:**
1. Gross margin at 61% — is this the floor?
2. OpEx +31% vs revenue +12% — wrong direction
3. "AI infrastructure" — vague, no ROI timeline given
4. Free cash flow likely compressed
5. "On track" — on track to what exactly?

**Verdict:** Mixed quarter. Skepticism warranted until management gives specifics.

---

### 🔵 Sonnet 4.6

> Balanced. Analytical. Actionable.

**Is this healthy?** No — and the math proves it.

**The gross margin problem is worse than it looks:**
- Prior gross profit (assumed $1B revenue): **$680M**
- Current gross profit ($1.12B × 61%): **$683M**
- Result: $120M more revenue → only **$3M more gross profit**
- The company is growing revenue at near-zero incremental economics

**Key flags:**

| Priority | Issue |
|---|---|
| 🚨 Critical | Gross margin — is 61% the floor or still falling? |
| 🚨 Critical | AI spend — total amount, CapEx vs. OpEx treatment, ROI timeline |
| 🔴 High | OpEx breakdown by R&D / S&M / G&A — which line is at 31%? |
| 🔴 High | When does OpEx growth normalize below revenue growth? |
| 🟡 Medium | Free cash flow impact |
| 🟡 Medium | Revenue quality — NRR, mix, cohort data |
| 🟡 Medium | Are peers spending similarly on AI? |

> "AI infrastructure" without dollar amounts is a narrative, not a commitment.
> "On track" without a destination is not a trackable statement.

**Verdict:** Not healthy. Show-me posture until management provides investment amounts, ROI framework, and margin recovery timeline.

---

### 🟣 Opus 4.6

> Deep. Comprehensive. Institutional-grade.

**Is this healthy?** No — and here is the precise calculation that shows how bad it is.

**Incremental gross margin — the key insight:**

| Item | Math | Result |
|---|---|---|
| Prior gross profit | $1,000M × 68% | $680M |
| Current gross profit | $1,120M × 61% | $683M |
| Extra revenue generated | — | $120M |
| Extra gross profit generated | — | **~$3M** |
| **Incremental gross margin** | $3M ÷ $120M | **~2.5%** |

The headline margin is 61%. The *real* margin on new revenue is **2.5%**. That is the actual problem.

**Why OpEx +31% is structural, not a blip:**
- For every 1% of revenue growth, costs grew 2.6% — negative operating leverage
- CapEx vs. OpEx classification of AI spend dramatically changes reported income — management has not disclosed which treatment they use
- One-time vs. recurring split unknown

**"AI infrastructure" — three possible realities:**
- ✅ Best case: strategic platform buildout with clear 3-year payback
- ⚠️ Neutral: competitive catch-up spending, uncertain payoff
- ❌ Worst case: undisciplined spend dressed in AI language

**Analyst flags (P0 = ask in earnings call today):**

| Priority | Flag |
|---|---|
| P0 | Gross margin target for next 4 quarters — is 61% the trough? |
| P0 | AI spend in dollars — CapEx or OpEx? Payback timeline? |
| P1 | OpEx split by function (R&D / S&M / G&A) |
| P1 | CapEx vs. OpEx accounting policy — what does operating income look like either way? |
| P1 | When does OpEx growth fall below revenue growth? |
| P2 | Free cash flow this quarter |
| P2 | NRR, cohort data, revenue mix |
| P2 | Peer AI spending comparison |
| P3 | Define "on track" — specific metrics and timeline |

**Verdict:** Value destruction in the short term. The AI bet may pay off — but it is a hypothesis, not a conclusion. Maintain cautious rating until P0 questions are answered.

> *The stock may price in the optimistic scenario. The analyst's job is to price in the realistic one.*

---

## Head-to-Head Verdict

### 🏆 Best Overall — Sonnet 4.6

Sonnet hits **85% of Opus's analytical depth at half the length.** It does the critical math, flags the accounting issue, tiers its recommendations, and delivers a verdict a real analyst can act on — all in a format you can read in two minutes.

### 🔬 Deepest Analysis — Opus 4.6

Opus is the only model that calculates the **2.5% incremental gross margin** — the single most important insight in this analysis. If you're writing research for an institutional client or preparing for a tough earnings Q&A, Opus is the right tool.

### ⚡ Fastest Triage — Haiku 4.5

Haiku gets the direction right, quickly. Good for automated screening or a first-pass alert. Not a substitute for real analysis.

---

## When to Use Each Model

| Situation | Use |
|---|---|
| Quick internal alert or screening | **Haiku** |
| Standard quarterly analysis | **Sonnet** |
| Institutional research / initiating coverage | **Opus** |
| High volume + occasional deep dives | **Haiku → escalate to Sonnet** |

---

## Key Takeaways

1. **All three models got the direction right** — this is not a healthy quarter. They differ only in depth, not conclusion.
2. **The 2.5% incremental margin** is the insight that separates Opus from the rest. It reframes the severity completely.
3. **CapEx vs. OpEx treatment of AI spend** is the most underrated flag — only Sonnet and Opus caught it.
4. **"AI infrastructure" is not an explanation.** It is a placeholder. Any model over ~600 words will push back on it.
5. **Prompt engineering closes the Haiku gap.** Adding "perform the gross profit math and tier your flags" pushes Haiku much closer to Sonnet.

---

*Tested June 2026 · Claude Haiku 4.5 · Sonnet 4.6 · Opus 4.6 · No system prompt · Default settings*
