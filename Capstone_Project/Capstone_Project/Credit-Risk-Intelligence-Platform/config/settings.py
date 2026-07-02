# config/settings.py
# ============================================================
# All application configuration — loaded from .env file.
# Import `settings` everywhere; never read os.environ directly.
#
# Architecture:
#   LLM_PROVIDER         = Gemini (text generation, summaries, answers)
#   EMBEDDING_PROVIDER   = OpenAI (creates vectors for search)
#   VECTOR_STORE_PROVIDER= faiss (local) or pinecone (cloud/production)
# ============================================================
from __future__ import annotations
from pathlib import Path
from typing import Literal
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────
    APP_TITLE:      str = "Credit Risk Intelligence Platform"
    APP_ENV:        Literal["development", "staging", "production"] = "development"
    LOG_LEVEL:      str = "INFO"
    LOG_FILE:       str = "logs/app.log"
    DATA_UPLOAD_DIR: str = "data/uploads"

    # ── LLM Provider (text generation) ───────────────────────
    # groq   = Groq (PRIMARY — fastest, generous free tier, no credit card)
    # openai = OpenAI GPT-4o (SECOND fallback)
    # gemini = Google Gemini (THIRD fallback)
    LLM_PROVIDER: Literal["openai", "gemini", "groq"] = "openai"

    # ── Embedding Provider (vector search) ───────────────────
    EMBEDDING_PROVIDER: Literal["openai", "gemini"] = "openai"

    # ── Groq (PRIMARY LLM) ────────────────────────────────────
    # Free tier: 14,400 requests/day — no credit card needed
    # Get key at: https://console.groq.com
    GROQ_API_KEY:   str = ""
    GROQ_MODEL:     str = "llama-3.3-70b-versatile"

    # ── OpenAI (SECOND fallback) ──────────────────────────────
    OPENAI_API_KEY:         str   = ""
    OPENAI_MODEL:           str   = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str   = "text-embedding-3-small"
    # Must match your Pinecone index's dimension exactly.
    # text-embedding-3-small supports custom dims from 1-1536 via OpenAI's
    # native dimension-reduction feature (no quality loss for most RAG use).
    # Set this to match whatever your Pinecone index was created with.
    OPENAI_EMBEDDING_DIMENSIONS: int = 1024
    OPENAI_TEMPERATURE:     float = 0.1
    OPENAI_MAX_TOKENS:      int   = 2048

    # ── Google Gemini ─────────────────────────────────────────
    GEMINI_API_KEY:         str   = ""
    GEMINI_MODEL:           str   = "gemini-2.0-flash"
    GEMINI_EMBEDDING_MODEL: str   = "models/text-embedding-004"
    GEMINI_TEMPERATURE:     float = 0.1
    GEMINI_MAX_TOKENS:      int   = 2048

    # ── Vector Store Provider ─────────────────────────────────
    # faiss   = local (works offline, no external service needed)
    # pinecone= cloud production (requires PINECONE_API_KEY)
    VECTOR_STORE_PROVIDER: Literal["faiss", "pinecone"] = "faiss"

    # ── FAISS (local vector store) ───────────────────────────
    FAISS_INDEX_PATH: str = "data/vectorstore/faiss_index"

    # ── Pinecone (cloud vector store — production) ────────────
    PINECONE_API_KEY:    str = ""
    PINECONE_INDEX_NAME: str = "credit-risk-platform"
    PINECONE_REGION:     str = "us-east-1"

    # ── RAG Configuration ─────────────────────────────────────
    CHUNK_SIZE:      int = 1000   # chars per chunk (was 600, increased for financial tables)
    CHUNK_OVERLAP:   int = 200    # overlap between chunks (was 250)
    RETRIEVER_TOP_K: int = 6      # BUG FIX: was 12 (too noisy); 6 with MMR is optimal
    RETRIEVER_USE_MMR: bool = True # Use Maximal Marginal Relevance for diversity
    RETRIEVER_SCORE_THRESHOLD: float = 0.0  # Min cosine score to include chunk (0.0 = off)

    # Hybrid search (BM25 + vector) and year-aware re-ranking — added to fix
    # cross-year hallucinations found in evaluation (see src/retrieval/reranker.py)
    HYBRID_SEARCH_ENABLED: bool = True
    RERANK_ENABLED: bool = True

    # ── OCR (optional, for scanned PDFs) ─────────────────────
    OCR_ENABLED:            bool = True
    TESSERACT_CMD:          str  = ""
    OCR_MIN_CHARS_PER_PAGE: int  = 50

    # ── LangSmith Observability (optional, free tier) ─────────
    LANGCHAIN_API_KEY:    str  = ""
    LANGCHAIN_PROJECT:    str  = "credit-risk-platform"
    LANGCHAIN_TRACING_V2: bool = False

    # ── Evaluation (backend-only, not visible in UI) ──────────
    EVALUATION_ENABLED:   bool = False  # Set true to enable RAGAS + DeepEval
    DEEPEVAL_API_KEY:     str  = ""     # Get free key at app.confident-ai.com

    # ── FastAPI Backend ───────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_KEY:  str = ""    # Optional: protects FastAPI endpoints with Bearer token

    # ── Retirement Planner defaults ───────────────────────────
    RETIREMENT_DEFAULT_RETURN:    float = 14.0   # % annual return
    RETIREMENT_DEFAULT_INFLATION: float = 6.0    # % annual inflation
    RETIREMENT_DEFAULT_LIFE_EXP:  int   = 80     # years

    # ── Authentication ─────────────────────────────────────────
    JWT_SECRET_KEY:       str  = "change-this-in-production-use-a-random-64-char-string"
    SESSION_EXPIRY_HOURS: int  = 24

    # ── Email (optional — SMTP for password reset / verification) ──
    # If left blank, emails are safely logged to logs/dev_emails.log
    # instead of crashing the app. Gmail example: smtp.gmail.com, port 587,
    # use an "app password" (not your real password) for SMTP_PASSWORD.
    SMTP_HOST:     str = ""
    SMTP_PORT:     int = 587
    SMTP_USER:     str = ""
    SMTP_PASSWORD: str = ""

    # ── Validators ────────────────────────────────────────────
    @field_validator("LOG_LEVEL")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()

    def ensure_directories(self) -> None:
        for path_str in [
            self.DATA_UPLOAD_DIR,
            "data/vectorstore/faiss_index",
            str(Path(self.LOG_FILE).parent),
            "data/demo",
        ]:
            Path(path_str).mkdir(parents=True, exist_ok=True)

    # ── Computed properties ───────────────────────────────────
    @property
    def active_llm_model(self) -> str:
        return self.GEMINI_MODEL if self.LLM_PROVIDER == "gemini" else self.OPENAI_MODEL

    @property
    def active_embedding_model(self) -> str:
        if self.EMBEDDING_PROVIDER == "openai":
            return self.OPENAI_EMBEDDING_MODEL
        return self.GEMINI_EMBEDDING_MODEL

    @property
    def langsmith_enabled(self) -> bool:
        return bool(self.LANGCHAIN_API_KEY) and self.LANGCHAIN_TRACING_V2

    @property
    def ocr_available(self) -> bool:
        return self.OCR_ENABLED

    @property
    def pinecone_configured(self) -> bool:
        return bool(self.PINECONE_API_KEY) and self.VECTOR_STORE_PROVIDER == "pinecone"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
settings.ensure_directories()
