# src/services/langsmith_setup.py
# ============================================================
# LangSmith Observability Setup
#
# LangChain auto-traces all LLM calls when these three
# environment variables are set before any LangChain import:
#   LANGCHAIN_TRACING_V2=true
#   LANGCHAIN_API_KEY=ls__...
#   LANGCHAIN_PROJECT=your-project-name
#
# This module reads them from settings and writes them into
# os.environ at startup. Called once from app.py.
#
# What gets traced automatically (no code changes needed):
#   - Every LLM call (input prompt, output, latency, tokens)
#   - Every embedding generation
#   - Every RAG retrieval step
#   - Every chain / agent execution
#
# View traces at: https://smith.langchain.com
# ============================================================

from __future__ import annotations

import os

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def initialise() -> None:
    """
    Activate LangSmith tracing by writing required env vars.
    Call this once at application startup, before any LangChain
    objects are created.
    """
    if not settings.LANGCHAIN_API_KEY:
        logger.info(
            "LangSmith tracing DISABLED — LANGCHAIN_API_KEY not set. "
            "Get a free key at https://smith.langchain.com"
        )
        return

    if not settings.LANGCHAIN_TRACING_V2:
        logger.info(
            "LangSmith tracing DISABLED — LANGCHAIN_TRACING_V2=false in .env. "
            "Set to true to enable tracing."
        )
        return

    # Write to os.environ — LangChain reads these at import time
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"]    = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"]    = settings.LANGCHAIN_PROJECT

    logger.info(
        "LangSmith tracing ENABLED — Project: '%s'. "
        "View traces at https://smith.langchain.com",
        settings.LANGCHAIN_PROJECT,
    )


def status() -> dict[str, str]:
    """
    Return current LangSmith configuration status.
    Used by the UI to display observability status.
    """
    return {
        "enabled":  str(settings.langsmith_enabled),
        "project":  settings.LANGCHAIN_PROJECT,
        "key_set":  "Yes" if settings.LANGCHAIN_API_KEY else "No",
        "tracing":  "Active" if settings.langsmith_enabled else "Inactive",
    }
