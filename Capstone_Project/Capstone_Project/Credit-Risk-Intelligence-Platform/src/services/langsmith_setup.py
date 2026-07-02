# src/services/langsmith_setup.py
# ============================================================
# LangSmith Observability Setup — v3.2
#
# Traces the FULL user journey, not just LLM calls:
#   login → document upload → processing → risk analysis → chat
#
# Every function decorated with @traceable appears as a named
# span in LangSmith, showing inputs, outputs, latency, errors.
#
# Works for BOTH local and Azure deployment — traces go directly
# to smith.langchain.com regardless of where the app runs.
# ============================================================
from __future__ import annotations
import os
import functools
import time
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def initialise() -> None:
    """Activate LangSmith tracing. Call once at app startup."""
    if not settings.LANGCHAIN_API_KEY:
        logger.info("LangSmith tracing DISABLED — LANGCHAIN_API_KEY not set.")
        return
    if not settings.LANGCHAIN_TRACING_V2:
        logger.info("LangSmith tracing DISABLED — LANGCHAIN_TRACING_V2=false.")
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"]    = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"]    = settings.LANGCHAIN_PROJECT

    logger.info(
        "LangSmith tracing ENABLED — Project: '%s'. "
        "View traces at https://smith.langchain.com",
        settings.LANGCHAIN_PROJECT,
    )


def trace_span(name: str, run_type: str = "chain", metadata: dict | None = None):
    """
    Decorator that creates a LangSmith span for any function.

    Usage:
        @trace_span("document_upload", run_type="chain", metadata={"component": "upload"})
        def process_document(self, file):
            ...

    In LangSmith this shows as a named span with:
    - Function name and run type
    - Input arguments
    - Return value
    - Time taken
    - Any errors that occurred
    - Metadata tags for filtering

    Works as a no-op (does nothing) when LangSmith is not configured,
    so the app works normally even without an API key.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not settings.langsmith_enabled:
                return func(*args, **kwargs)
            try:
                from langsmith import traceable
                traced = traceable(
                    name=name,
                    run_type=run_type,
                    metadata=metadata or {},
                )(func)
                return traced(*args, **kwargs)
            except Exception:
                # If tracing fails for any reason, run the function normally
                return func(*args, **kwargs)
        return wrapper
    return decorator


def status() -> dict[str, str]:
    return {
        "enabled": str(settings.langsmith_enabled),
        "project": settings.LANGCHAIN_PROJECT,
        "key_set": "Yes" if settings.LANGCHAIN_API_KEY else "No",
        "tracing": "Active" if settings.langsmith_enabled else "Inactive",
    }
