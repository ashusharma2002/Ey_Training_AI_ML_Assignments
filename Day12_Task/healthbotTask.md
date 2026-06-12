# HealthBot: Clinical RAG at Enterprise Scale

## Problem Statement

A large hospital network requires an AI-powered clinical assistant for 3,000 clinicians. The system must answer questions from more than 2 million pages of:

- Clinical guidelines
- Drug interaction documents
- Internal protocols and policies

### Requirements

- End-to-end response time < 3 seconds
- Answer accuracy > 92%
- HIPAA compliant
- Azure-only data residency
- Support for dense clinical text, lists, and tables

---

# Architecture Decision 1: Azure AI Search vs Weaviate on AKS

## Recommended Choice: Azure AI Search (Hybrid Search)

### Justification

The organization is a healthcare enterprise with strict compliance requirements.

Azure AI Search provides:

- Native Azure integration
- Azure AD authentication
- RBAC support
- HIPAA compliance support
- Hybrid Search (BM25 + Vector Search)
- Managed infrastructure
- Enterprise SLA

Since the requirement specifies Azure-only deployment and healthcare compliance, Azure AI Search is the most suitable solution.

### Why Not Weaviate?

Although Weaviate provides flexibility and open-source deployment:

- Requires AKS cluster management
- Higher operational overhead
- More DevOps effort
- Additional work for compliance controls

For an enterprise healthcare environment, compliance and maintainability are more important than infrastructure flexibility.

### Decision

**Azure AI Search (Hybrid)**

---

# Architecture Decision 2: Chunk Size (256 vs 1024 Tokens)

## Recommended Choice: 256 Tokens

### Justification

Clinical documents contain:

- Drug dosage information
- Contraindications
- Treatment guidelines
- Medical procedures
- Tables and bullet lists

Smaller chunks improve retrieval precision.

### Example

Question:

"What is the dosage adjustment for Drug X in renal impairment?"

A 1024-token chunk may contain:

- Dosage information
- Side effects
- Contraindications
- Storage instructions

The retrieval system may return irrelevant information.

A 256-token chunk isolates the relevant section and improves retrieval quality.

### Comparison

| Feature | 256 Tokens | 1024 Tokens |
|----------|----------|----------|
| Retrieval Precision | High | Medium |
| Hallucination Risk | Low | Higher |
| Context Quality | Better | Mixed |
| Search Accuracy | Higher | Lower |

### Decision

**256 Tokens**

---

# Architecture Decision 3: Claude Large Context Window vs RAG

## Recommended Choice: Retrieval-Augmented Generation (RAG)

### Justification

The knowledge base contains more than 2 million pages.

Even large-context models cannot efficiently process all information.

Problems with Context-Only Approach:

- High token cost
- Increased latency
- Poor scalability
- Reduced retrieval precision

Benefits of RAG:

- Retrieves only relevant documents
- Lower latency
- Lower cost
- Better factual grounding
- Easier compliance

### When Can RAG Be Skipped?

RAG can be skipped for:

- Small documents
- Session-based follow-up questions
- One-page summaries

Example:

"Summarize this discharge report."

No retrieval required.

### Decision

**Retrieval-Augmented Generation (RAG)**

---

# Architecture Decision 4: Multi-Index Strategy

## Recommended Choice: Separate Indexes Per Clinical Domain

### Proposed Index Structure

1. Cardiology
2. Oncology
3. Neurology
4. Pediatrics
5. Pharmacy
6. Internal Protocols

### Benefits

### Improved Accuracy

Question:

"What are the latest chemotherapy guidelines?"

The search is limited to the Oncology index.

### Faster Retrieval

Smaller indexes reduce search complexity.

### Better Governance

Departments can manage their own content independently.

### Decision

**Multi-Index Architecture**

---

# Recommended End-to-End Architecture

```text
Clinical Documents
(PDFs, Guidelines, Protocols)
          |
          v
Document Ingestion
          |
          v
OCR + Table Extraction
          |
          v
Semantic Chunking
(256 Tokens)
          |
          v
Embedding Generation
          |
          v
Azure AI Search
(Hybrid Index)
          |
     +----+----+
     |         |
     v         v
 BM25      Vector Search
     |         |
     +----+----+
          |
          v
      Rank & Merge
          |
          v
      Top-K Chunks
          |
          v
        Claude
          |
          v
   Clinical Answer
     + Citations
```

---

# Query Processing Flow

```text
Clinician Question
          |
          v
Hybrid Retrieval
(BM25 + Vector Search)
          |
          v
Retrieve Top-K Chunks
          |
          v
Reranking
          |
          v
Claude LLM
          |
          v
Grounded Clinical Answer
          |
          v
Source Citations
```

---

# Why Hybrid Search?

Clinical queries require both exact keyword matching and semantic understanding.

### BM25 Handles Exact Terms

Examples:

- BRCA1 mutation
- HER2 positive
- Troponin-I
- IL-6 inhibitor

### Vector Search Handles Meaning

Example:

"Which medications should be avoided in patients with kidney disease?"

Even if exact words differ, semantic search retrieves relevant information.

### Result

Combining BM25 and Vector Search provides:

- Higher accuracy
- Better recall
- Better precision

---

# Final Recommendations

| Component | Selected Option | Justification |
|------------|----------------|--------------|
| Search Engine | Azure AI Search (Hybrid) | HIPAA compliance and Azure integration |
| Chunk Size | 256 Tokens | Better retrieval precision |
| Knowledge Retrieval | RAG | Scalable for 2M+ pages |
| Index Strategy | Multi-Index | Better performance and governance |
| Retrieval Method | Hybrid BM25 + Vector | Exact + Semantic matching |
| Compliance | Azure-only Deployment | HIPAA and data residency requirements |

---

# Conclusion

The recommended architecture for HealthBot is:

- Azure AI Search (Hybrid Search)
- 256-token semantic chunking
- Retrieval-Augmented Generation (RAG)
- Multi-index clinical architecture
- BM25 + Vector hybrid retrieval
- Claude as the answer generation layer

This architecture satisfies all business requirements:

- Less than 3 seconds latency
- More than 92% answer accuracy
- HIPAA compliance
- Azure-only data residency
- Enterprise-scale deployment for 3,000 clinicians