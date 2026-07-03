# 🏦 Credit Risk Intelligence Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?style=flat-square&logo=streamlit)
![Azure](https://img.shields.io/badge/Azure-App_Service-0078D4?style=flat-square&logo=microsoft-azure)
![Docker](https://img.shields.io/badge/Docker-Containerised-2496ED?style=flat-square&logo=docker)
![Tests](https://img.shields.io/badge/Tests-96_passing-brightgreen?style=flat-square)
![LangSmith](https://img.shields.io/badge/LangSmith-Observability-orange?style=flat-square)

**AI-powered credit risk assessment for individual customers and financial institutions.**

[🌐 Live App](https://creditriskplatform.azurewebsites.net) · [📊 LangSmith Traces](https://smith.langchain.com) · [🐙 GitHub Actions](../../actions)

</div>

---

## 👥 Team

| Name | Role |
|---|---|
| **Akash Chaurasiya** | Full Stack + AI Pipeline |
| **Ashu Sharma** | Full Stack + Azure Deployment |

**EY Training 2026 · Capstone Project · Day 5 Submission**

---

## 🎯 What This Solves

Banks receive hundreds of loan applications. Officers manually read 50–100 page PDFs per application — taking 3–5 days, producing inconsistent decisions. Our platform:

- **Processes documents in seconds** — not days
- **Gives consistent, explainable AI decisions** — not subjective human judgement
- **Works for both sides** — individual customers AND bank loan officers

---

## 🚀 Live Demo

```
https://creditriskplatform.azurewebsites.net
```

Upload any of the test profiles from `data/test_profiles/` to see a full risk assessment instantly.

---

## ✨ Key Features

### For Individual Customers
| Feature | Description |
|---|---|
| 🔐 **Secure Login** | JWT + bcrypt authentication. Passwords never stored in plain text |
| 📤 **Upload PDFs** | Salary slips, bank statements, credit reports, ITR, loan statements |
| 📊 **Risk Analysis** | AI-generated credit score (0–100) with strengths, weaknesses, red flags |
| 🏦 **Loan Assessment** | Approval probability, safe borrowing amount, recommended banks |
| 💡 **AI Recommendations** | Urgency-sorted action plan: Critical → High → Moderate → Low |
| 💬 **AI Chat** | Ask any question about your own documents — grounded answers only |
| 🏙️ **Retirement Planner** | City-aware corpus calculator covering 40 Indian cities |

### For Financial Institutions (Banks)
| Feature | Description |
|---|---|
| 🏛️ **Executive Summary** | Structured applicant overview for loan officers |
| 🚨 **Fraud Detection** | Unexplained cash spikes, round-number patterns, income inconsistencies |
| 📈 **NPA + CRAR Metrics** | Bank-specific indicators — never shown to individual customers |
| ✅ **Loan Decision** | Approve / Approve with conditions / Reject with clear reasoning |

---

## 🏗️ Architecture

```
Browser (Streamlit UI)
    └── app.py  ─── Auth Gate (JWT)
         ├── ui/pages/auth.py               Login · Register · Forgot Password
         ├── ui/pages/upload.py             Document upload + loan gate
         ├── ui/pages/summary.py            AI document summary
         ├── ui/pages/risk_analysis.py      Risk score + loan assessment
         ├── ui/pages/recommendations.py    AI recommendations
         ├── ui/pages/chat.py               Validated AI chat
         └── ui/pages/retirement_planner.py City-aware retirement planning
              └── src/orchestrator/orchestrator.py
                   ├── src/agents/document_agent.py     PDF extraction
                   ├── src/agents/retrieval_agent.py    Hybrid search + re-ranking
                   ├── src/agents/chat_agent.py         All LLM calls
                   ├── src/retrieval/reranker.py        BM25 + year-aware ranking
                   ├── src/llm/llm_factory.py           OpenAI → Groq → Gemini fallback
                   ├── src/auth/                        JWT + SQLite
                   └── src/retirement/city_data.py      40-city dataset
```

### LLM Fallback Chain
```
OpenAI (gpt-4o-mini)  →  Groq (llama-3.3-70b)  →  Gemini (gemini-2.0-flash)
     PRIMARY                   FALLBACK                    BACKUP
```
If any provider hits quota or rate limits, the next one takes over automatically. Fully transparent to users.

---

## 🧪 Test Profiles

Six fictional customer PDFs in `data/test_profiles/` for reproducible testing:

| Profile | Person | CIBIL | Expected Result |
|---|---|---|---|
| `01_young_salaried` | Rohan Mehta, 26 | 742 | Conditional approval |
| `02_mid_career` | Priya Nair, 38 | 801 | Strong approval |
| `03_small_business` | Arjun Patel, 45 | 695 | Review required |
| `04_high_income` | Dr. Kavita Iyer, 52 | 835 | Easy approval |
| `05_bad_credit` | Deepak Sharma, 34 | 511 | Rejection — 3 defaults, 78% DTI |
| `06_struggling_biz` | Meena Pillai, 41 | 548 | Rejection — declining revenue |

---

## 📊 AI Quality — Evaluation Results

We measure AI quality using **DeepEval** (hallucination detection) and **RAGAS** (faithfulness + relevancy).

| Metric | Bad Profile | Good Profile | Threshold |
|---|---|---|---|
| DeepEval Hallucination Score | **0.217** ✅ | **0.283** ✅ | < 0.5 |
| Grounded Answers | **9/10** ✅ | **8/10** ✅ | > 7/10 |
| Trap Questions Refused | **2/2** ✅ | **2/2** ✅ | 2/2 |

**62% reduction in hallucination** achieved by hybrid BM25 + vector search with year-aware re-ranking.

Full results: `tests/evaluation/results/`

---

## 🔬 Testing — 96 Unit Tests

```bash
python -m pytest tests/unit/ -v
# Result: 96 passed, 1 skipped in ~6 seconds
# No API keys required
```

| Test File | Tests | Covers |
|---|---|---|
| `test_auth.py` | 13 | Login, register, JWT, bcrypt, password reset |
| `test_loan_workflow.py` | 16 | Loan gate, prompt branching, institution vs customer |
| `test_entity_aware_fixes.py` | 19 | Bank=NPA/CRAR, Individual=DTI, never crossed |
| `test_reranker.py` | 14 | BM25 hybrid, year-aware re-ranking |
| `test_city_and_validator.py` | 13 | 40-city dataset, autocomplete, missing doc detection |
| `test_retirement_calc.py` | 4 | Corpus maths, city-adjusted expenses |
| `test_sampling.py` | 5 | Financial content extraction |
| `test_schemas.py` | 6 | Data models, risk score bounds |

---

## ⚙️ CI/CD Pipeline

Two GitHub Actions workflows run automatically on every push to `main`:

| Workflow | Purpose |
|---|---|
| `main.yml` | Quality gate — runs 96 tests + builds Docker image |
| `main_creditriskplatform.yml` | Azure deploy — builds image → pushes to ACR → deploys |

```
git push origin main
    → Tests run (96 unit tests)
    → Docker image built and pushed to Azure Container Registry
    → Azure App Service pulls new image and restarts
    → App live at creditriskplatform.azurewebsites.net
```

---

## 👁️ Observability — LangSmith

Every user action is traced in LangSmith — login, document upload, risk analysis, chat. No local run needed — traces appear directly from the live Azure app.

```bash
# Enable in .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=credit-risk-platform
```

Named spans: `auth.login_attempt` → `document_upload_complete` → `run_risk_analysis` → `retrieval_agent.retrieve` → `chat_agent.answer_question`

---

## 🐳 Docker

```bash
# Build
docker build -f infra/Dockerfile -t credit-risk-platform:latest .

# Run locally
docker run -p 8501:8501 --env-file .env credit-risk-platform:latest

# Open
open http://localhost:8501
```

---

## ☁️ Azure Deployment

| Resource | Name |
|---|---|
| Container Registry | `creditriskakash7272.azurecr.io` |
| App Service Plan | `credit-risk-plan` (B2 — 2 CPU, 3.5GB RAM) |
| Web App | `creditriskplatform.azurewebsites.net` |

Full deployment runbook: [`docs/deployment_runbook.md`](docs/deployment_runbook.md)

---

## 🛠️ Local Setup

### 1. Clone

```bash
git clone https://github.com/Chaurasiyakash0136/EY-Training-2026.git
cd EY-Training-2026/Capstone_Project/Credit-Risk-Intelligence-Platform
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your real API keys
```

Required keys:

| Key | Where to Get |
|---|---|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `GROQ_API_KEY` | https://console.groq.com (free) |
| `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey |
| `PINECONE_API_KEY` | https://app.pinecone.io |
| `LANGCHAIN_API_KEY` | https://smith.langchain.com (optional) |
| `JWT_SECRET_KEY` | Any random 32+ character string |

### 5. Run

```bash
streamlit run app.py
```

Open http://localhost:8501

### 6. Run Tests

```bash
python -m pytest tests/unit/ -v
```

---

## 📁 Project Structure

```
Credit-Risk-Intelligence-Platform/
├── app.py                          # Main entry point
├── requirements.txt                # All dependencies (pinned)
├── .env.example                    # Environment template
├── config/
│   └── settings.py                 # Pydantic settings
├── src/
│   ├── agents/                     # Document, Retrieval, Chat agents
│   ├── auth/                       # JWT + SQLite authentication
│   ├── llm/                        # OpenAI, Groq, Gemini providers
│   ├── orchestrator/               # Coordinates all agents
│   ├── retrieval/                  # BM25, vector store, re-ranker
│   ├── retirement/                 # 40-city retirement calculator
│   └── services/                   # LangSmith observability
├── ui/
│   ├── pages/                      # All Streamlit pages
│   └── theme.py                    # Full dark theme
├── tests/
│   ├── unit/                       # 96 unit tests
│   └── evaluation/                 # DeepEval + RAGAS evaluation
├── infra/
│   ├── Dockerfile                  # Container definition
│   └── docker-compose.yml          # Local container setup
├── data/
│   └── test_profiles/              # 6 fictional test customer PDFs
└── docs/
    └── deployment_runbook.md       # Full deployment documentation
```

---

## 📈 Project Stats

| Metric | Value |
|---|---|
| **Total lines of code (Python + Docs)** | **11,625** |
| Python lines | **10,491** |
| Python files | **77** |
| `src/` — Core backend (agents, LLM, auth, retrieval) | 4,696 lines |
| `ui/` — All Streamlit pages + dark theme | 3,660 lines |
| `tests/` — Unit tests + evaluation framework | 1,270 lines |
| `config/` — Settings + Pydantic models | 178 lines |
| `app.py` — Main entry point | 128 lines |
| Docs + YAML + Config files | 1,134 lines |
| Unit tests passing | **96** |
| Test profiles (fictional customers) | **6** |
| Indian cities in retirement planner | **40** |
| LLM providers with automatic fallback | **3** |
| Hallucination score (bad credit profile) | **0.217** |
| Hallucination reduction vs baseline | **62%** (from 0.58) |

---

## 📄 License

Built for EY Training 2026 Capstone. All test profile data is entirely fictional.
