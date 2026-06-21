# 💼 FinSight — Financial RAG System

An end-to-end Retrieval-Augmented Generation (RAG) pipeline for querying SEC 10-K filings using natural language.

## 🎯 What this does

Ask questions like:
> "What was Apple's total revenue in fiscal 2023?"

And get back:
> "Apple's total revenue in fiscal 2023 was $383.3 billion. [Source: Apple_10K_2023_Risk]"

## 🏗️ Project Structure

```
financial_rag_system/
│
├── src/                          # All source code
│   ├── config.py                 # Credentials & settings
│   ├── documents.py              # Document loading (10-K data)
│   ├── chunker.py                # Text chunking logic
│   ├── embedder.py               # HuggingFace embeddings + FAISS
│   ├── retriever.py              # MMR retriever setup
│   ├── generator.py              # Azure OpenAI GPT-4o chain
│   ├── evaluator.py              # RAGAS evaluation
│   └── hybrid.py                 # Hybrid retrieval + re-ranker
│
├── data/
│   └── sample_docs/              # 10-K text excerpts
│
├── tests/
│   └── test_pipeline.py          # Basic tests
│
├── scripts/
│   └── run_pipeline.py           # Main runner script
│
├── notebooks/
│   └── exploration.ipynb         # Jupyter notebook (optional)
│
├── .env.example                  # Template for credentials
├── .env                          # Your actual credentials (git-ignored)
├── .gitignore
├── requirements.txt
└── README.md
```

## ⚙️ Setup

### 1. Clone & create virtual environment
```bash
git clone <your-repo-url>
cd financial_rag_system
python -m venv venv
source venv/bin/activate          # Mac/Linux
venv\Scripts\activate             # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure credentials
```bash
cp .env.example .env
# Edit .env and fill in your Azure OpenAI keys
```

### 4. Run the pipeline
```bash
python scripts/run_pipeline.py
```

## 🔑 Required credentials (in .env)
- `AZURE_OPENAI_ENDPOINT` — your Azure OpenAI resource URL
- `AZURE_OPENAI_KEY` — your API key
- `AZURE_OPENAI_DEPLOYMENT` — your GPT-4o deployment name (e.g. `gpt-4o`)

## 📊 Target metrics
| Metric | Target |
|--------|--------|
| Faithfulness | ≥ 0.85 |
| Latency | < 3s |
| Cost per query | < $0.002 |
