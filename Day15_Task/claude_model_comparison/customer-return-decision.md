# Claude Model Comparison — Customer Return Policy Decision

![Models](https://img.shields.io/badge/models-Haiku_·_Sonnet_·_Opus-blue)
![Task](https://img.shields.io/badge/task-Customer_Service_Decision-green)
![Winner](https://img.shields.io/badge/best_overall-Sonnet_4.6-blueviolet)

Same prompt. Three models. Who reasons better?

---

## The Prompt

```
A customer bought a jacket 47 days ago. Your return policy is 45 days.
The customer says the zipper broke on day 44 but they were travelling.
No receipt, but the order is in your system. They're a 6-year customer
with 23 orders. Should you accept the return? Write one paragraph with reasoning.
```

---

## Quick Comparison

| Criterion | Haiku 4.5 | Sonnet 4.6 | Opus 4.8 |
|---|---|---|---|
| **Correct decision** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Defect vs. exception distinction** | ❌ Absent | ✅ Explicit | ✅ Detailed |
| **Communication strategy** | ❌ None | ✅ Recommended | ✅ Detailed |
| **Lifetime value analysis** | ⚠️ Mentioned | ✅ Framed | ✅ Quantified |
| **Risk / precedent consideration** | ❌ None | ⚠️ Implicit | ✅ Explicit |
| **Documentation guidance** | ❌ None | ❌ None | ✅ Yes |
| **Conciseness** | ✅ High | ✅ Balanced | ⚠️ Verbose |
| **Actionability** | ✅ High | ✅ High | ✅ High |
| **Policy framework utility** | ❌ Low | ✅ Medium | ✅ High |
| **Best for** | Quick triage | Daily decisions | Policy design |

---

## Model Responses + Strengths & Weaknesses

---

### 🟢 Haiku 4.5

**Response:**

> Yes, accept the return. The zipper broke during the return window (day 44), and the
> brief 2-day delay is justified by travel. A 6-year customer with 23 orders is valuable
> — losing them over a late return caused by a product defect is not worth it. The order
> is confirmed in your system, so no receipt is needed. Accept the return to preserve
> the relationship.

**✅ Strengths**
- Direct and decisive — no ambiguity in the answer
- Identifies customer lifetime value as a factor
- Fast and easy to understand
- Appropriate for rapid decision-making

**❌ Weaknesses**
- Does not distinguish between a *defect claim* vs. a *late return exception* — treats them as the same issue
- Minimal exploration of policy implications
- Does not frame the communication strategy for the customer
- Lacks depth on risk and precedent considerations

---

### 🔵 Sonnet 4.6

**Response:**

> Yes — frame this as a defect resolution, not a policy exception. A zipper breaking on
> day 44 is a product failure, not a late return; the 45-day window governs change-of-mind
> returns, and a 2-day overage caused by a manufacturing defect is distinct from a customer
> simply deciding they don't want the jacket anymore. The order in your system is stronger
> proof than a paper receipt. The real consideration is customer lifetime value: a 6-year,
> 23-order customer represents significant repeat revenue, and refusing them over two days
> and a broken zipper would be a false economy. Accept the return, make the distinction
> explicit in your response (*"we treat defects differently from late change-of-mind
> returns"*), and use it as a service recovery moment.

**✅ Strengths**
- Distinguishes defect claim from late return — a critical nuance
- Recommends a specific communication strategy
- Balances policy integrity with customer value
- Frames the decision as goodwill, not capitulation
- Appropriate length and depth for a professional context

**❌ Weaknesses**
- Does not explore edge cases or precedent risk
- Could have mentioned documentation for future reference
- Slight assumption that the zipper failure can be verified (not addressed)

---

### 🟣 Opus 4.8

**Response:**

> Yes, absolutely accept the return — and here's why this decision is straightforward if
> you separate three things that are often conflated. First: the zipper failed on day 44,
> which is within your 45-day window. The fact that the customer didn't report it until
> day 47 is a *reporting lag*, not a *defect-discovery lag* — the failure itself is
> on-policy. Second: the distinction between "product defect" and "policy exception" is
> critical. Your 45-day window exists to balance buyer's remorse (which should be
> time-limited) with the need for customers to catch problems and report them. A zipper
> breaking is a manufacturing failure, not a case of the customer changing their mind,
> so treating it as a policy override misdiagnoses the issue entirely. Third: customer
> lifetime value. This is a 6-year customer with 23 orders — that's roughly $150–300k
> in lifetime revenue depending on jacket price. The cost of a replacement or refund is
> likely under $200, making this a 750:1 return-on-investment just in terms of retention.
> The missing receipt is irrelevant because your order system provides the necessary
> verification. Accept the return, document it as a defect claim (not a policy exception),
> and communicate the reason to the customer so they understand you're backing your product
> quality, not bending rules on demand. This turns a potential reputation risk into a
> loyalty moment.

**✅ Strengths**
- Most rigorous breakdown of the decision logic
- Explains the distinction between defect and exception with authority
- Calculates lifetime value and shows the math (750:1 ROI)
- Addresses reputational risk explicitly
- Recommends documentation approach
- Most useful for building a defensible policy going forward
- Anticipates how the customer will perceive the decision

**❌ Weaknesses**
- Longer response — may be overkill for a simple front-line decision
- More verbose than necessary for operational speed
- Makes assumptions about price point (though reasonable ones)

---

## Verdict

### 🏆 Best Overall — Sonnet 4.6

Sonnet delivers the optimal balance for a real-world customer service decision. It surfaces
the critical **defect vs. exception** distinction, provides a concrete communication
strategy, and is immediately actionable — all without the verbosity of Opus. A customer
service manager can read it, decide, and respond to the customer in under two minutes.

### 🔬 Deepest Reasoning — Opus 4.8

Opus is the right tool when you're **building or refining a policy**, not handling a single
case. It quantifies lifetime value ($150–300k vs. a <$200 refund), separates the decision
into three distinct logical layers, and provides a documentation recommendation — giving
you a reusable framework for future similar decisions.

### ⚡ Fastest Answer — Haiku 4.5

Haiku is correct and quick. Best for high-volume automated triage where the case is
clear-cut. Not suitable for edge cases — it misses the key nuance that protects your
policy from precedent misuse.

---

## When to Use Each Model

| Situation | Use |
|---|---|
| Front-line support agent, high-volume chat | **Haiku 4.5** |
| Customer service manager approving edge cases | **Sonnet 4.6** |
| Building or refining a return / warranty policy | **Opus 4.8** |
| Automated triage with human escalation | **Haiku → Sonnet** |

---

## The Critical Insight

> **Defect claim ≠ Policy exception**

The 45-day window limits *buyer's remorse* — not *product defects*. A broken zipper on
day 44 is a manufacturing failure. Treating it as a late return sets a dangerous precedent
(anyone can ask for 2 extra days). Treating it as a defect keeps your policy intact.

**Only Sonnet and Opus caught this. Haiku did not.**

---

## Optimised Prompt

The original prompt works. For more consistent output — especially with Haiku — use this:

```
You are a customer service decision-maker. A customer requests a return:

Customer profile : 6-year account, 23 orders
Product          : jacket purchased 47 days ago
Policy           : 45-day return window
Claim            : zipper broke on day 44; customer was travelling until day 47
Receipt          : not available, but order confirmed in system

1. Make a clear yes/no recommendation.
2. Distinguish between a defect claim vs. a policy exception.
3. Suggest how to frame the response to the customer.
4. Factor in customer lifetime value.
5. Note any precedent or documentation considerations.
```

**Why it's better:** Forces every model to address the defect/exception distinction,
communication strategy, and documentation — the three areas where Haiku falls short
on the plain prompt.

---

## Summary

| Model | One line verdict |
|---|---|
| **Haiku 4.5** | Right answer, wrong depth — doesn't give you tools for the next case |
| **Sonnet 4.6** | Right answer, right depth — gives you the decision, reasoning, and what to say |
| **Opus 4.8** | Right answer, maximum depth — gives you a decision framework for the whole category |

For most customer service teams, **Sonnet is the best fit.**

---

*Tested June 2026 · Claude Haiku 4.5 · Sonnet 4.6 · Opus 4.8 · No system prompt · Default settings*
