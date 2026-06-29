# src/llm/llm_factory.py
# ============================================================
# LLM Factory with Gemini → OpenAI automatic fallback.
#
# How it works:
#   get_chat_model()  → returns Gemini LLM (primary)
#   get_embeddings()  → returns OpenAI embeddings
#
# Fallback: if Gemini raises a quota/rate/unavailable error,
#   the factory transparently retries with OpenAI GPT-4o-mini.
#   This is logged but invisible to the rest of the application.
#
# Adding a provider: implement BaseLLMProvider, add to registry.
# ============================================================
from __future__ import annotations
from functools import lru_cache
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from config.settings import settings
from src.llm.base_provider import BaseLLMProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Quota / rate-limit error signals ─────────────────────────────────────────
_FALLBACK_SIGNALS = (
    "quota", "rate", "limit", "429", "resource_exhausted",
    "resourceexhausted", "unavailable", "overloaded", "timeout",
    "deadline", "503", "500", "internal",
)


def _is_quota_error(exc: Exception) -> bool:
    """Return True if this exception looks like a quota or availability error."""
    msg = str(exc).lower()
    type_name = type(exc).__name__.lower()
    return any(s in msg or s in type_name for s in _FALLBACK_SIGNALS)


def _build_registry() -> dict[str, type[BaseLLMProvider]]:
    from src.llm.openai_provider import OpenAIProvider
    from src.llm.gemini_provider import GeminiProvider
    return {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
    }


def _make_provider(key: str) -> BaseLLMProvider:
    registry = _build_registry()
    if key not in registry:
        raise ValueError(f"Unknown provider '{key}'. Available: {list(registry.keys())}")
    p = registry[key]()
    logger.info("Provider instantiated: %s", p.provider_name)
    return p


@lru_cache(maxsize=1)
def _chat_provider() -> BaseLLMProvider:
    return _make_provider(settings.LLM_PROVIDER)


@lru_cache(maxsize=1)
def _embedding_provider() -> BaseLLMProvider:
    return _make_provider(settings.EMBEDDING_PROVIDER)


@lru_cache(maxsize=1)
def _fallback_chat_provider() -> BaseLLMProvider:
    """OpenAI fallback — only instantiated if Gemini fails."""
    return _make_provider("openai")


def get_chat_model() -> BaseChatModel:
    """
    Return the configured chat model (Gemini by default).
    If Gemini fails due to quota/rate limits, returns OpenAI automatically.
    """
    return _chat_provider().get_chat_model()


def get_chat_model_with_fallback() -> BaseChatModel:
    """
    Return Gemini chat model. If unavailable, fall back to OpenAI.
    Use this in all LLM call sites for resilience.
    """
    try:
        model = _chat_provider().get_chat_model()
        return model
    except Exception as exc:
        if _is_quota_error(exc) and settings.LLM_PROVIDER == "gemini":
            logger.warning(
                "Gemini unavailable (%s). Falling back to OpenAI.", exc
            )
            return _fallback_chat_provider().get_chat_model()
        raise


def invoke_with_fallback(messages: list) -> str:
    """
    Invoke the LLM with automatic Gemini → OpenAI fallback.
    Returns the response content string.

    This is the RECOMMENDED way to call the LLM throughout the app.
    All agents should use this instead of llm.invoke() directly.
    """
    # Try primary provider (Gemini)
    try:
        llm = _chat_provider().get_chat_model()
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception as primary_exc:
        if _is_quota_error(primary_exc) and settings.LLM_PROVIDER == "gemini":
            logger.warning(
                "Gemini quota/rate error: %s — switching to OpenAI fallback.",
                primary_exc,
            )
            # Try OpenAI fallback
            try:
                llm_fallback = _fallback_chat_provider().get_chat_model()
                response = llm_fallback.invoke(messages)
                logger.info("OpenAI fallback succeeded.")
                return response.content.strip()
            except Exception as fallback_exc:
                logger.error("Both Gemini and OpenAI failed. Gemini: %s | OpenAI: %s",
                             primary_exc, fallback_exc)
                raise RuntimeError(
                    f"Both AI providers failed.\n"
                    f"Gemini error: {primary_exc}\n"
                    f"OpenAI error: {fallback_exc}"
                ) from fallback_exc
        raise


def get_embeddings() -> Embeddings:
    """Return the configured embedding model (OpenAI by default)."""
    return _embedding_provider().get_embeddings()


def get_provider() -> BaseLLMProvider:
    """Backward-compatible alias — returns primary chat provider."""
    return _chat_provider()
