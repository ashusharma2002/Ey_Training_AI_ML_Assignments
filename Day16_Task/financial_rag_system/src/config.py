"""
config.py — loads all credentials from .env and exposes settings.
All other modules import from here — never hardcode keys anywhere else.
"""

import os
from dotenv import load_dotenv

# Load .env file automatically
load_dotenv()

# ─── Azure OpenAI ─────────────────────────────────────────────────────────────
AZURE_ENDPOINT    = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY     = os.getenv("AZURE_OPENAI_KEY")
AZURE_DEPLOYMENT  = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_API_VERSION = "2024-06-01"

# ─── HuggingFace ──────────────────────────────────────────────────────────────
HF_TOKEN = os.getenv("HF_TOKEN")

# ─── Embedding model ──────────────────────────────────────────────────────────
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cpu"   # change to "cuda" if you have a GPU

# ─── Chunking defaults ────────────────────────────────────────────────────────
CHUNK_SIZE    = 512
CHUNK_OVERLAP = 64

# ─── Retriever defaults ───────────────────────────────────────────────────────
RETRIEVER_K       = 4    # chunks returned per query
RETRIEVER_FETCH_K = 10   # candidate pool for MMR
RETRIEVER_LAMBDA  = 0.7  # 1.0 = pure relevance, 0.0 = pure diversity

# ─── LLM settings ─────────────────────────────────────────────────────────────
LLM_TEMPERATURE = 0      # deterministic — important for financial answers
LLM_MAX_TOKENS  = 512
LLM_TIMEOUT     = 30


def validate_credentials():
    """Call this at startup to catch missing credentials early."""
    missing = []
    if not AZURE_ENDPOINT:
        missing.append("AZURE_OPENAI_ENDPOINT")
    if not AZURE_API_KEY:
        missing.append("AZURE_OPENAI_KEY")
    if not AZURE_DEPLOYMENT:
        missing.append("AZURE_OPENAI_DEPLOYMENT")

    if missing:
        raise EnvironmentError(
            f"\n❌ Missing credentials in .env: {', '.join(missing)}\n"
            "   Copy .env.example → .env and fill in your Azure OpenAI keys.\n"
        )
    print("✅ Credentials loaded successfully")
