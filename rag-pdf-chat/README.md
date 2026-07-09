# 📄 RAG PDF Chat

A small end-to-end RAG (Retrieval-Augmented Generation) project:
Upload PDFs → ask questions → get grounded answers with sources.

**Stack:** pypdf + Gemini (embeddings + generation) + Pinecone (vector DB) + Streamlit (UI)
**Deployment:** Docker + GitHub Actions CI/CD + Azure App Service

---

## 1. Local Setup

### Prerequisites
- Python 3.11+
- A Gemini API key: https://aistudio.google.com/app/apikey
- A Pinecone API key (free tier): https://www.pinecone.io/

### Steps
```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your environment variables
copy .env.example .env       # Windows
cp .env.example .env         # Mac/Linux
# Now edit .env and paste in your real API keys

# 4. Add PDFs
# Put 1-3 PDF files into data/pdfs/

# 5. Run the CLI version
python main.py

# 6. OR run the Streamlit UI version
streamlit run app.py
```

---

## 2. Run with Docker (local)

```bash
docker build -t rag-pdf-chat .
docker run -p 8501:8501 --env-file .env rag-pdf-chat
```

Visit http://localhost:8501

---

## 3. Deploy to Azure (CI/CD)

See step-by-step guide provided separately. Summary:
1. Create Azure Container Registry (ACR)
2. Create Azure App Service (Web App for Containers)
3. Add GitHub Secrets: `ACR_USERNAME`, `ACR_PASSWORD`, `AZURE_WEBAPP_PUBLISH_PROFILE`
4. Update `.github/workflows/deploy.yml` with your ACR + App Service names
5. Push to `main` branch → GitHub Actions builds, tests, and deploys automatically

---

## Project Structure
```
rag-pdf-chat/
├── data/pdfs/              # put your PDFs here
├── src/
│   ├── ingest.py            # PDF loading
│   ├── chunk.py             # text chunking
│   ├── embed_store.py       # Gemini embeddings + Pinecone storage
│   ├── retriever.py         # similarity search
│   ├── generator.py         # Gemini answer generation
│   └── pipeline.py          # orchestrates everything
├── tests/test_pipeline.py   # basic tests
├── main.py                  # CLI entry point
├── app.py                   # Streamlit UI
├── Dockerfile
├── .github/workflows/deploy.yml
└── requirements.txt
```
