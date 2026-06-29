# config/settings.py
# ============================================================
# All application configuration — loaded from .env file.
# Never read os.environ directly elsewhere. Import `settings`.
#
# Architecture:
#   LLM_PROVIDER       = Gemini (generates text, summaries, answers)
#   EMBEDDING_PROVIDER = OpenAI (creates vectors for search)
#   These are INDEPENDENT — best of both providers.
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
    # gemini = Google Gemini (default, cost-effective)
    # openai = OpenAI GPT-4o (used as fallback when Gemini quota exceeded)
    LLM_PROVIDER: Literal["openai", "gemini"] = "gemini"

    # ── Embedding Provider (vector search) ───────────────────
    # openai = text-embedding-3-small (best quality, independent of LLM)
    EMBEDDING_PROVIDER: Literal["openai", "gemini"] = "openai"

    # ── OpenAI ────────────────────────────────────────────────
    OPENAI_API_KEY:        str   = ""
    OPENAI_MODEL:          str   = "gpt-4o-mini"   # fallback model
    OPENAI_EMBEDDING_MODEL: str  = "text-embedding-3-small"
    OPENAI_TEMPERATURE:    float = 0.1
    OPENAI_MAX_TOKENS:     int   = 2048

    # ── Google Gemini ─────────────────────────────────────────
    GEMINI_API_KEY:        str   = ""
    GEMINI_MODEL:          str   = "gemini-1.5-pro"
    GEMINI_EMBEDDING_MODEL: str  = "models/text-embedding-004"
    GEMINI_TEMPERATURE:    float = 0.1
    GEMINI_MAX_TOKENS:     int   = 2048

    # ── RAG / FAISS Vector Store ──────────────────────────────
    FAISS_INDEX_PATH: str   = "data/vectorstore/faiss_index"
    CHUNK_SIZE:       int   = 600
    CHUNK_OVERLAP:    int   = 250
    RETRIEVER_TOP_K:  int   = 12  # chunks retrieved per query

    # ── OCR (optional, for scanned PDFs) ─────────────────────
    OCR_ENABLED:           bool = True
    TESSERACT_CMD:         str  = ""   # Windows: C:\Program Files\Tesseract-OCR\tesseract.exe
    OCR_MIN_CHARS_PER_PAGE: int = 50

    # ── LangSmith Observability (optional) ───────────────────
    LANGCHAIN_API_KEY:     str  = ""
    LANGCHAIN_PROJECT:     str  = "credit-risk-platform"
    LANGCHAIN_TRACING_V2:  bool = False

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
            str(Path(self.FAISS_INDEX_PATH).parent),
            str(Path(self.LOG_FILE).parent),
            "data/demo",
        ]:
            Path(path_str).mkdir(parents=True, exist_ok=True)

    @property
    def active_llm_model(self) -> str:
        return self.GEMINI_MODEL if self.LLM_PROVIDER == "gemini" else self.OPENAI_MODEL

    @property
    def active_embedding_model(self) -> str:
        return self.OPENAI_EMBEDDING_MODEL if self.EMBEDDING_PROVIDER == "openai" else self.GEMINI_EMBEDDING_MODEL

    @property
    def langsmith_enabled(self) -> bool:
        return bool(self.LANGCHAIN_API_KEY) and self.LANGCHAIN_TRACING_V2

    @property
    def ocr_available(self) -> bool:
        return self.OCR_ENABLED


settings = Settings()
settings.ensure_directories()
