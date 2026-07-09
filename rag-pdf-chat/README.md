# 📄 RAG PDF Chat

A small end-to-end RAG (Retrieval-Augmented Generation) project:
Upload PDFs → ask questions → get grounded answers with sources.

**Live demo:** https://rag-pdf-chat-axcvekhtfwhebuhz.centralindia-01.azurewebsites.net

**Stack:** pypdf + Gemini API (embeddings + generation) + Pinecone (vector DB) + Streamlit (UI)
**Deployment:** GitHub Actions CI/CD + Azure App Service (code-based deploy via Oryx, no Docker)

---

## Architecture

```
PDF files
   │
   ▼
pypdf (extract text)
   │
   ▼
Custom chunker (text_chunker.py)
   │
   ▼
Gemini Embeddings (gemini-embedding-001)
   │
   ▼
Pinecone (vector storage + similarity search)
   │
   ▼
Gemini Generation (gemini-flash-latest)
   │
   ▼
Streamlit UI (chat interface)
```

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

## 2. Deployment (Azure App Service — no Docker)

This project is deployed using **code-based ZIP deployment**, not containers.
Docker wasn't used because the development VM didn't support hardware
virtualization required by Docker Desktop. Instead, Azure's built-in **Oryx**
build system installs dependencies and runs the app directly using Azure's
native Python runtime.

### One-time Azure setup
1. Create a **Resource Group**
2. Create an **App Service Plan** (Linux, Basic B1 or higher — Free tier may
   not be available on all subscriptions)
3. Create a **Web App**:
   - Publish: **Code**
   - Runtime stack: **Python 3.11**
   - OS: **Linux**
4. In **Configuration → General settings**:
   - Enable **SCM Basic Auth Publishing Credentials** (needed to download the
     publish profile)
5. In **Configuration → Stack settings**:
   - Set **Startup Command** to `startup.sh`
6. In **Configuration → Environment variables**, add:
   - `GEMINI_API_KEY`
   - `PINECONE_API_KEY`
   - `PINECONE_INDEX_NAME`
   - `SCM_DO_BUILD_DURING_DEPLOYMENT` = `true` (tells Azure to run
     `pip install -r requirements.txt` after deployment)
7. Download the **Publish Profile** (Overview page → Download publish
   profile)

### GitHub setup
1. Add a repository secret: `AZURE_WEBAPP_PUBLISH_PROFILE` (paste the full
   contents of the downloaded publish profile file)
2. Make sure `.github/workflows/deploy.yml` lives at the **repository root**
   — GitHub Actions only reads workflow files from `.github/workflows/` at
   the root, not from a project subfolder
3. Push to the `main` (or your default) branch — GitHub Actions will
   automatically:
   - Install dependencies
   - Run tests (`pytest tests/`)
   - Deploy the code to Azure App Service using the publish profile

---

## Issues encountered & fixed along the way

| Issue | Fix |
|---|---|
| `chunk.py` collided with Python's built-in `chunk` module | Renamed to `text_chunker.py` |
| Gemini embedding model `text-embedding-004` deprecated | Switched to `gemini-embedding-001`, updated Pinecone index dimension from 768 → 3072 |
| Gemini generation model `gemini-2.0-flash` deprecated (then `2.5-flash` too) | Switched to the `gemini-flash-latest` alias so it auto-tracks the current stable model |
| Docker Desktop failed — VM lacked virtualization support | Switched deployment strategy from Docker/ACR to Azure's native code-based deploy (Oryx build) |
| GitHub Actions workflow not detected | Moved `deploy.yml` from a project subfolder to the repository's root `.github/workflows/` folder |
| First deploy failed — "No module named streamlit" | Added `SCM_DO_BUILD_DURING_DEPLOYMENT=true` so Azure actually installs `requirements.txt` |
| Deploy failed once with "SCM container restart" conflict | Retried after waiting a couple of minutes for Azure's backend to settle |
| Free-tier Gemini rate limit (5 requests/minute) | Expected on free tier — space out requests when testing |

---

## Project Structure
```
rag-pdf-chat/
├── data/pdfs/                    # put your PDFs here (not committed)
├── src/
│   ├── ingest.py                  # PDF loading
│   ├── text_chunker.py            # text chunking
│   ├── embed_store.py             # Gemini embeddings + Pinecone storage
│   ├── retriever.py                # similarity search
│   ├── generator.py                # Gemini answer generation
│   └── pipeline.py                 # orchestrates everything
├── tests/test_pipeline.py         # basic tests (run in CI)
├── main.py                        # CLI entry point
├── app.py                         # Streamlit UI
├── startup.sh                     # tells Azure how to start the app
├── Dockerfile                     # kept for future local Docker practice
│                                     (not used in current deployment)
└── requirements.txt
```

Note: `.github/workflows/deploy.yml` lives at the **repository root**, not
inside this project folder, since GitHub Actions requires workflow files to
be located there.

---

## Possible next steps
- Revisit Docker locally via GitHub Codespaces (the original dev VM couldn't
  run Docker Desktop due to a virtualization limitation)
- Add a "Build/Rebuild Index" trigger as part of CI/CD instead of a manual
  Streamlit sidebar button
- Add retry/backoff logic around Gemini API calls to gracefully handle
  free-tier rate limits
