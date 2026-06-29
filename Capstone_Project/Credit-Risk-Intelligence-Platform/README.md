# 🏦 Credit Risk Intelligence Platform

> Enterprise MVP — AI-powered credit risk analysis, document intelligence, and RAG-based advisory

---

## Overview

The Credit Risk Intelligence Platform is an enterprise-grade Streamlit application that transforms financial document review from a multi-hour manual process into a minutes-long AI-assisted workflow.

Built for **credit analysts** at commercial lending banks and **loan applicants** tracking their applications.

---

## Features

| Feature | Description |
|---|---|
| 📤 Document Upload | Bank statements, ITR, balance sheets, P&L — PDF upload with processing |
| 📋 AI Summaries | Executive summaries, income/expense/asset/liability breakdowns |
| 🔍 Risk Analysis | Scored risk assessment (0–100), strengths, red flags, credit health |
| 💡 Recommendations | Credit improvement checklist, safer loan options, next actions |
| 💬 AI Chat | RAG-powered chatbot grounded exclusively in uploaded documents |
| 📊 Dashboard | KPI cards, risk gauge, activity feed, AI insights |

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Chaurasiyakash0136/EY-Training-2026
cd credit-risk-platform
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

Set your LLM provider:

```env
LLM_PROVIDER=openai          # or: gemini
OPENAI_API_KEY=sk-...
```

### 5. Run the application

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Project Structure

```
credit-risk-platform/
├── app.py                        # Main entry point
├── requirements.txt
├── .env.example
├── config/
│   └── settings.py               # Centralised configuration (pydantic-settings)
├── src/
│   ├── agents/
│   │   ├── document_agent.py     # Agent 1: PDF extraction + summarisation
│   │   ├── retrieval_agent.py    # Agent 2: FAISS embedding + retrieval
│   │   ├── recommendation_chat_agent.py  # Agent 3: chat + risk + recommendations
│   │   └── orchestrator.py       # Lightweight multi-agent coordinator
│   ├── llm/
│   │   ├── base_provider.py      # Abstract provider interface
│   │   ├── openai_provider.py    # OpenAI implementation
│   │   ├── gemini_provider.py    # Google Gemini implementation
│   │   └── llm_factory.py        # Provider registry + singleton
│   ├── rag/
│   │   ├── loader.py             # PDF text extraction (PyMuPDF + pypdf fallback)
│   │   ├── chunker.py            # RecursiveCharacterTextSplitter (pluggable)
│   │   ├── vector_store.py       # FAISS index management
│   │   └── prompt_builder.py     # Prompt templates for each agent task
│   ├── models/
│   │   └── schemas.py            # Pydantic v2 data models
│   ├── ui/
│   │   ├── theme.py              # Banking-grade CSS + component library
│   │   ├── sidebar.py            # Navigation + status panel
│   │   └── pages/
│   │       ├── dashboard.py
│   │       ├── upload.py
│   │       ├── summary.py
│   │       ├── risk_analysis.py
│   │       ├── recommendations.py
│   │       └── chat.py
│   ├── services/
│   │   └── observability.py      # Future: LangSmith / Azure Monitor stub
│   ├── utils/
│   │   └── logger.py             # Centralised logging
│   └── evaluation/               # Future: RAGAS / DeepEval placeholder
├── data/
│   ├── uploads/                  # Temporary PDF storage
│   └── vectorstore/              # Persisted FAISS index
└── logs/                         # Application logs
```

---

## LLM Providers

Switch between providers with a single `.env` change:

```env
LLM_PROVIDER=openai    # Uses GPT-4o + text-embedding-3-small
LLM_PROVIDER=gemini    # Uses Gemini 1.5 Pro + text-embedding-004
```

### Adding a new provider

1. Create `src/llm/your_provider.py` implementing `BaseLLMProvider`
2. Register it in `src/llm/llm_factory.py`
3. Add its settings to `.env.example`

No other changes needed anywhere.

---

## Architecture

### Multi-Agent Pipeline

```
User uploads PDF
      ↓
Agent 1 (DocumentIntelligenceAgent)
  • PyMuPDF text extraction
  • AI-generated JSON summary
  • Document chunking
      ↓
Agent 2 (RetrievalAgent)
  • Embedding generation
  • FAISS index update
      ↓
Agent 3 (RecommendationChatAgent)
  • Risk scoring (structured JSON)
  • Credit recommendations
  • RAG-grounded chat answers
      ↓
AgentOrchestrator (coordinator)
  • Routes data between agents
  • Updates PlatformState
  • Returns results to UI
```

### RAG Pipeline

```
Query → Retrieve top-k chunks → Build prompt → LLM → Grounded answer
```

---

## Roadmap

The following capabilities are **architecturally planned** but not yet implemented:

- **OCR Pipeline** — Azure Document Intelligence, Google Document AI, Tesseract
- **Enterprise RAG** — Hybrid search, parent-child retrieval, re-ranking, citations
- **Observability** — LangSmith, Azure Monitor, token/cost tracking
- **Evaluation** — RAGAS, DeepEval, TruLens
- **Deployment** — Docker, Azure Container Apps, Azure AI Search, Cosmos DB
- **Security** — Auth, RBAC, Azure Key Vault, PII masking
- **Testing** — Unit, integration, RAG evaluation, E2E tests

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | OpenAI GPT-4o / Google Gemini 1.5 Pro |
| Framework | LangChain |
| Vector DB | FAISS |
| PDF Parsing | PyMuPDF |
| Data | Pandas |
| Charts | Plotly |
| Validation | Pydantic v2 |
| Config | python-dotenv + pydantic-settings |

---

## Repository

GitHub: https://github.com/Chaurasiyakash0136/EY-Training-2026
