"""
config.py — loads credentials from .env (local) or Streamlit secrets (cloud).
All other modules import from here — never hardcode keys anywhere else.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def _get(key, default=None):
    """Read from env first, then Streamlit secrets if running on cloud."""
    val = os.getenv(key, default)
    if not val:
        try:
            import streamlit as st
            val = st.secrets.get(key, default)
        except Exception:
            pass
    return val

# ─── Azure OpenAI ─────────────────────────────────────────────────────────────
AZURE_ENDPOINT    = _get("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY     = _get("AZURE_OPENAI_KEY")
AZURE_DEPLOYMENT  = _get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_API_VERSION = "2024-06-01"

# ─── HuggingFace ──────────────────────────────────────────────────────────────
HF_TOKEN = _get("HF_TOKEN")

# ─── Embedding model ──────────────────────────────────────────────────────────
EMBEDDING_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cpu"

# ─── Chunking defaults ────────────────────────────────────────────────────────
CHUNK_SIZE    = 512
CHUNK_OVERLAP = 64

# ─── Retriever defaults ───────────────────────────────────────────────────────
RETRIEVER_K       = 4
RETRIEVER_FETCH_K = 10
RETRIEVER_LAMBDA  = 0.7

# ─── LLM settings ─────────────────────────────────────────────────────────────
LLM_TEMPERATURE = 0
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
            f"\n❌ Missing credentials: {', '.join(missing)}\n"
            "   Add them to .env (local) or Streamlit Cloud secrets (deployed).\n"
        )
    print("✅ Credentials loaded successfully")
