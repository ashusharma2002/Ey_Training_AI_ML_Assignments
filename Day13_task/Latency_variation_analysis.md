# Day 13 – Task 1

# Analysis of RAG Pipeline Latency Variation Using BLEU, ROUGE, and Faithfulness Metrics

## Objective

Analyze the latency variation observed in the Day 12 Colab 2 RAG Pipeline and explain the behavior in terms of:

- BLEU Score
- ROUGE Score
- Faithfulness Score
- RAG Pipeline Stages

---

# Graph Overview

The graph shows latency contribution from three stages of a Retrieval-Augmented Generation (RAG) pipeline:

1. Embed Query (Blue)
2. Azure Retrieve (Orange)
3. Claude Generate (Green)

Queries are represented as Q1–Q8.

A red dotted line represents the average total latency.

---

# Observations from the Graph

| Query | Approx Total Latency |
|---------|---------------------|
| Q1 | ~800 ms |
| Q2 | ~900 ms |
| Q3 | ~9700 ms |
| Q4 | ~5000 ms |
| Q5 | ~6000 ms |
| Q6 | ~7800 ms |
| Q7 | ~8100 ms |
| Q8 | ~5400 ms |

### Key Observation

The blue (Embedding) and orange (Retrieval) portions remain almost constant across all queries.

The green (Claude Generation) portion varies significantly and dominates total latency.

Therefore:

> Latency variation is primarily caused by the Claude Generation stage.

---

# Stage-Wise Analysis

## 1. Embedding Stage

Purpose:

- Convert user query into vector embeddings.

Characteristics:

- Fixed model.
- Similar token count for all queries.
- Stable execution time.

Observed Latency:

~200–500 ms

Impact on Variation:

Very Low

---

## 2. Retrieval Stage

Purpose:

- Search Azure Vector Database.
- Retrieve relevant documents/chunks.

Characteristics:

- Similar retrieval configuration.
- Fixed top-k retrieval.
- Stable database response.

Observed Latency:

~250–500 ms

Impact on Variation:

Low

---

## 3. Claude Generation Stage

Purpose:

- Generate final answer using retrieved context.

Characteristics:

- Depends on:
  - Context length
  - Prompt size
  - Output size
  - Reasoning complexity

Observed Latency:

~300 ms to ~9000 ms

Impact on Variation:

Very High

---

# Why Claude Generation Causes Latency Variation

## Case 1: Larger Retrieved Context

More retrieved chunks result in:

- More input tokens
- Longer prompt processing

Thus:

Higher latency

---

## Case 2: Longer Generated Answers

If Claude generates:

- Detailed explanations
- Summaries
- Comparisons

Then output token count increases.

Thus:

Higher latency

---

## Case 3: Complex Reasoning

Questions requiring:

- Multi-document synthesis
- Logical reasoning
- Comparative analysis

Need more inference steps.

Thus:

Higher latency

---

# Relationship with BLEU Score

## What is BLEU?

BLEU (Bilingual Evaluation Understudy) measures how closely generated text matches a reference answer.

Higher BLEU means:

- More overlap with expected answer.
- Better answer quality.

### Impact on Latency

To achieve higher BLEU:

- More relevant context may be retrieved.
- More detailed generation may be performed.

Result:

Higher generation time.

### Interpretation for Graph

Queries such as:

- Q3
- Q6
- Q7

Likely generated longer and more complete answers.

Therefore:

- Higher BLEU
- Higher latency

---

# Relationship with ROUGE Score

## What is ROUGE?

ROUGE evaluates:

- Recall
- Coverage of important information

It measures how much of the reference answer is captured.

Higher ROUGE means:

- More information retained.
- More comprehensive responses.

### Impact on Latency

To maximize ROUGE:

- Claude generates longer responses.
- More retrieved content is utilized.

Result:

Higher latency.

### Interpretation for Graph

Queries with very high generation time likely attempted to cover more information.

Therefore:

- Higher ROUGE
- Higher latency

---

# Relationship with Faithfulness Score

## What is Faithfulness?

Faithfulness measures whether generated content is supported by retrieved documents.

Formula:

Faithfulness =
Supported Statements / Total Statements

Higher faithfulness means:

- Less hallucination
- More grounded responses

---

## Impact on Latency

To maintain high faithfulness:

1. More documents may be retrieved.
2. More evidence must be processed.
3. Claude performs additional grounding against retrieved context.

Result:

Longer generation time.

---

# Interpretation of High-Latency Queries

## Q3

Highest latency (~9700 ms)

Possible reasons:

- Large retrieved context.
- Long answer generation.
- Extensive reasoning.
- High faithfulness verification.

Expected Metrics:

- High BLEU
- High ROUGE
- High Faithfulness

---

## Q6 and Q7

Latency ~7800–8100 ms

Possible reasons:

- Rich context retrieval.
- Comprehensive answer generation.
- Better grounding.

Expected Metrics:

- High BLEU
- High ROUGE
- High Faithfulness

---

## Q1 and Q2

Latency <1000 ms

Possible reasons:

- Short prompts.
- Small context.
- Brief answers.

Expected Metrics:

- Moderate BLEU
- Moderate ROUGE
- Lower contextual coverage

---

# Correlation Between Metrics and Latency

| Metric | Effect on Latency |
|----------|------------------|
| BLEU ↑ | Latency ↑ |
| ROUGE ↑ | Latency ↑ |
| Faithfulness ↑ | Latency ↑ |
| Context Size ↑ | Latency ↑ |
| Output Length ↑ | Latency ↑ |

Reason:

Higher-quality answers generally require:

- More retrieved evidence
- More token processing
- More reasoning

which increases generation time.

---

# Final Conclusion

The graph clearly indicates that latency variation is not caused by the Embedding or Retrieval stages. The dominant contributor is the Claude Generation stage. Queries with higher latency likely involve larger retrieved contexts, longer responses, deeper reasoning, and stronger grounding to source documents.

Expressed in terms of evaluation metrics:

- Higher BLEU scores require more complete and accurate generation.
- Higher ROUGE scores require broader information coverage.
- Higher Faithfulness scores require stronger grounding in retrieved documents.

These factors increase token processing and reasoning effort inside the LLM, resulting in higher generation latency.

Therefore, the latency variation observed in the RAG pipeline is primarily a trade-off between response quality (BLEU, ROUGE, Faithfulness) and generation speed.