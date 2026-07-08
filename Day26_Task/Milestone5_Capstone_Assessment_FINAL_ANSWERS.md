# Milestone 5 Capstone Assessment — Answers
### Project: Credit Risk Intelligence Platform (Akash Chaurasiya & Ashu Sharma, EY Training 2026)

---

## SECTION A — Problem Framing & Data Strategy (20 marks · 25 min)

### Question 1 [10 marks]

**(a) ML problem statement**

Translating the stakeholder's vague ask into my domain: *"We're rejecting good applicants and approving bad ones — build us something to fix that."*

- **Target variable:** a 0–100 credit risk score, bucketed into an Approve / Review / Reject decision. The underlying construct that score is a proxy for is *probability of default or serious delinquency* — but since my platform scores applicants from uploaded documents (salary slips, bank statements, ITR, credit reports) rather than from a labeled loan-performance history, what I've actually built is a **point-in-time creditworthiness assessment**, not a true forward-looking default model.
- **Unit of analysis:** one loan application event (an applicant + their document set at a point in time), not "the customer" as a persistent entity — the same person reapplying six months later with different financials should get a different score.
- **Prediction window:** this is the honest gap to name to the stakeholder — a real forward-looking model needs a labeled outcome ("did this loan default within N months of disbursement"), which a document-scoring pipeline doesn't have by default. I'd propose a 12–24 month repayment-outcome window as the target for a future labeled version, and be explicit that the current system is a defensible interim proxy, not the end state.

**(b) Metrics**

*Business metrics:*
1. **Time-to-decision** — the core value proposition is going from days of manual review to minutes; if accuracy improves but officers still re-verify everything by hand, the business problem isn't solved.
2. **Approval rate among creditworthy applicants** — the "revenue loss" framing in the problem statement is about losing good customers to faster competitors, so this tracks whether the system is actually recovering that lost business, not just being technically accurate.

*ML metrics:*
1. **Faithfulness / groundedness of the generated explanation** (RAGAS-style) — a risk score is only useful if the reasoning behind it is traceable to real figures in the applicant's documents.
2. **Hallucination rate** (DeepEval-style, checking every claim against retrieved chunks) — proxies for whether the output can be trusted without a human re-verifying it line by line, which is the entire point of automating this step.

*Why a high ML metric alone isn't enough:* a system can score very well on faithfulness and still fail the stakeholder if it's too slow to use, if bank officers can't defend its output in an audit, or if it produces disparate outcomes across applicant subgroups (see Q7). None of those failure modes show up in a faithfulness or accuracy number — they only show up when you look at how the output is actually used downstream.

---

### Question 2 [10 marks]

*(Framing note: the specific % figures below are illustrative of the scenario as given — swap in your actual data-quality findings if you have them.)*

**(a) Triage/priority:** fix the unseen-category issue first; treat the timestamp corruption as a documented limitation rather than a silent patch. Reasoning: an unseen category (e.g., a new bank name, employment type, or loan type format the extraction/prompt logic has never encountered) tends to fail *silently* — it produces a wrong or missing value that flows straight into the score with no visible error. A corrupted timestamp usually fails *loudly* (a parse error, a missing date), which is a safer failure mode because it can be caught and flagged rather than quietly mis-scoring someone.

**(b) Remediation:**
- *Unseen categories:* bucket unrecognized values into an "Other/Unclassified" category with a confidence flag, rather than dropping the row or forcing a guess. Route ambiguous fields through a document-summary fallback (plain-language description) instead of a rigid schema field, so the information isn't lost even if it can't be structured.
- *Corrupted timestamps:* don't impute a fabricated date for financial documents — a wrong date on a bank statement can change which month's balance is being scored. Re-extract from the raw page first; if that fails, exclude the field from scoring and surface "date unverified" explicitly rather than defaulting to today's date or a median.

**(c) Known limitation to flag rather than silently fix:** the extraction and prompting logic is tuned against a specific set of document templates. A spike in unseen categories in the most recent month is a signal that document-format coverage is narrower than a demo might suggest — better to state that plainly in the report ("performance is validated against X document formats; unseen formats are not yet covered") than let the demo imply broader robustness than actually exists.

---

## SECTION B — Modeling & Evaluation (30 marks · 40 min)

### Question 3 [10 marks]

My system is an LLM + retrieval pipeline rather than a classical trained classifier, so the interpretability-vs-performance tradeoff shows up between model *configurations* rather than model *families* — e.g., a faster fallback model versus a slower, higher-quality primary model.

I'd keep the higher-quality, slower option as primary (with a faster fallback held in reserve) rather than optimizing purely for speed. The deciding factor beyond raw performance is **regulatory/audit defensibility**: a bank officer's Approve/Reject decision needs a written justification that could be scrutinized later. A faster but thinner explanation would undercut the entire stated goal — replacing manual review that was "inconsistent and hard to explain" — with something that's fast but equally hard to defend.

If a true trained classifier were involved (e.g., scoring DTI or NPA/CRAR thresholds), the same principle from the original scenario would apply directly: the simpler, interpretable model would be favored for the officer-facing decision, since that's the one that needs to survive an audit — a modest performance gap (e.g., 0.78 vs. 0.84 on a primary metric) is not worth losing that.

### Question 4 [10 marks]

Three plausible causes, most to least likely, for a document-grounded RAG pipeline like this:

1. **Temporal leakage / stale retrieval** — if validation happened to sit on a period where document dates matched the "current" prompt assumptions cleanly, and the held-out slice spans a different period, a re-ranking step that filters by recency could under-filter, letting outdated figures leak into the current answer.
2. **Document format drift** — a held-out time slice may include a new statement or report template that the text-extraction step wasn't tuned against, silently degrading everything downstream of it.
3. **Model/provider drift** — if the held-out run happened to fall back to a secondary LLM provider (due to rate limits or an outage), answer quality and hallucination rate could differ from what was seen in validation, since different providers aren't guaranteed to behave identically.

For the most likely cause (#1), the diagnostic check is: pull request traces for a sample of held-out-period queries and inspect what the retrieval step actually returned — specifically, do the retrieved chunks' document dates match the time period implied by the query? I'd also re-run the hallucination-detection check (DeepEval-style) on the held-out slice specifically, rather than only on the original validation set, and compare it against the baseline score — a regression back toward the pre-fix hallucination rate would confirm the re-ranker isn't generalizing to the new time period.

### Question 5 [10 marks]

*(Framing note: the "4%" figure below matches the scenario as given — replace with your dataset's actual class balance if you have it.)*

If the minority class of interest is "high-risk / Reject-worthy" applicants at roughly 4% of the pool, a model that predicts "Approve" for everyone scores **96% accuracy** while catching zero risky applicants — the opposite of what the system exists to do. Concretely: out of 1,000 applications, 40 are genuinely high-risk; a model that always says "Approve" gets all 960 low-risk applicants right and reports 96% accuracy, while missing all 40 high-risk cases it was built to catch.

Instead of accuracy, I'd present:
- **Recall on the high-risk class** — did the system catch the risky applicants at all. A missed high-risk approval (false negative) becomes an actual bad loan on the bank's books, discovered late and expensively.
- **Precision on the Reject/Review class**, alongside a faithfulness/hallucination check — because a false positive here (flagging a genuinely creditworthy applicant as high-risk) directly costs the bank a good customer, which is the exact "revenue loss" pain point in the original problem framing.

Cost asymmetry: a false negative (bad loan approved) is typically more expensive than a false positive (good applicant routed to manual Review instead of auto-Approved), since Review isn't a hard rejection — it routes to a human. That argues for biasing the system toward higher recall on the risky class, accepting more borderline-good applicants being sent to Review, rather than optimizing for headline accuracy.

---

## SECTION C — Deployment, Monitoring & Risk (25 marks · 35 min)

### Question 6 [10 marks]

**Data/feature drift checks:**
1. **Document-format drift** — track the share of monthly uploads landing in "Unclassified" buckets or failing document-completeness validation. Trigger: unclassified rate exceeding ~10% in a rolling week → investigate new document templates.
2. **Input distribution drift** — track the monthly distribution of extracted income and debt-to-income figures against a historical baseline. Trigger: a shift beyond ~1.5× the historical standard deviation in median DTI → investigate whether it's a genuine market shift or a broken extraction step.

**Performance-decay checks:**
1. **Hallucination score on a rolling sample of live traces** — sample and re-score live outputs weekly against the faithfulness/hallucination check used in evaluation. Trigger: rolling average regressing toward the pre-fix baseline → pause auto-decisions and route to manual review until root-caused.
2. **Fallback-provider usage rate** — track what share of requests are served by a secondary/fallback model instead of the primary. Trigger: fallback usage above ~20% for more than a day → investigate primary provider health, since quality can differ across providers even when errors aren't visible to the user.

**Action on breach:** not auto-retraining (no live-labeled feedback loop exists yet) — alert the platform owner, temporarily downgrade auto-decisions to "Review" instead of "Approve/Reject," and pull the relevant request traces to diagnose root cause before restoring normal operation.

### Question 7 [10 marks]

**(a) Subgroup analysis:** compare the Approve/Review/Reject distribution and average risk score across a sensitive subgroup (e.g., self-employed/SME applicants vs. salaried applicants, or applicants by region), while holding financial fundamentals — DTI, income, credit history — roughly constant. The specific metric to compare is **selection rate** (share approved) and **average score conditional on comparable fundamentals** across groups — if two applicants have near-identical DTI and repayment history but consistently different average scores based on group membership, that's the signal to investigate. I'd also audit whether entity-type branching logic (individual vs. institution scoring paths) is behaving as intended, since a bug in that branching could produce a systematic disparity that isn't actually a bias in the reasoning itself.

**(b) Mitigations:**
- *Data/feature level:* audit whether qualitative signals (e.g., "declining revenue" language, employment-type framing) are being weighted more harshly for one subgroup than the underlying numbers justify — i.e., check for a proxy variable effect rather than a true risk difference.
- *Model/decision level:* require every Approve/Review/Reject explanation to cite the specific financial figures behind it before finalizing (extending the same faithfulness check used for hallucination control) — this makes any subgroup-correlated pattern traceable back to a real number rather than an unexplained judgment call, and makes disparities auditable after the fact.

---

## SECTION D — Communication & Reflection (25 marks · 20 min)

### Question 8 [15 marks]

**(a) Plain-language explanation (≤120 words, ≤1 technical term):**

> "Our system flagged this application as high-risk because a large share of this person's monthly income is already going toward paying off existing debt — a ratio we call 'debt-to-income,' which just means how much of what they earn each month is already spoken for before any new loan payment. On top of that, their bank statements and credit report show a recent pattern of late payments. Neither factor alone would trigger a reject, but together they suggest little room to safely take on a new loan right now. We'd recommend either a smaller loan amount or a repayment plan on existing debt before reapplying."

(~110 words; one technical term — "debt-to-income" — defined inline.)

**(b) Interpretability technique:** the explanation is generated by a retrieval-grounded language-model pipeline — the model's output is constrained to reference facts pulled from the applicant's own uploaded documents via hybrid search, rather than a formal statistical attribution method like SHAP or a fixed feature-importance ranking. One real limitation: because it's language-generated rather than derived from a fixed numerical attribution, the explanation can still overstate or understate how much weight a given factor actually played — automated faithfulness checks can catch outright fabricated numbers, but they don't guarantee that relative-importance language ("primarily because of X") is numerically precise, only that the facts cited are real.

---

### Question 8 continued — Project Reflection

If I had one more week, the highest-leverage change would be **moving off SQLite to a managed auth/data store** (e.g., Supabase or Auth0). The evidence motivating this isn't a metric from a chart — it's a known operational failure mode: SQLite inside a container loses data on every redeploy, meaning every CI/CD-driven fix wipes user accounts and history. That's a bigger real-world reliability risk than a marginal gain in accuracy or hallucination rate, because it means the platform can't hold state across its own deployment cycle — and for a system handling real financial documents, silently losing user data on every deploy is a trust and compliance issue, not just an inconvenience.
