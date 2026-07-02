# src/llm/llm_factory.py
# ============================================================
# LLM Factory — 3-tier fallback chain
#
# PRIMARY:  Groq (llama-3.3-70b) — fastest, free 14,400 req/day
# SECOND:   OpenAI (gpt-4o-mini) — reliable, paid
# THIRD:    Gemini (gemini-2.0-flash) — backup, free tier
#
# If Groq quota is exhausted → auto-switches to OpenAI
# If OpenAI also fails → auto-switches to Gemini
# All failures are logged in LangSmith as warnings
# ============================================================
from __future__ import annotations
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Quota / rate-limit error signals
_FALLBACK_SIGNALS = (
    # Quota and rate limit errors
    "quota", "rate", "limit", "429", "resource_exhausted",
    "resourceexhausted", "unavailable", "overloaded", "timeout",
    "deadline", "503", "500", "internal", "exceeded",
    # Authentication errors — invalid/expired API key should also fallback
    "401", "authentication", "invalid api", "invalid_api",
    "unauthorized", "api key", "apikey", "not found", "404",
)

# Module-level provider cache
_chat_provider_cache      = None
_fallback_provider_cache  = None
_fallback2_provider_cache = None
_embedding_provider_cache = None


def _is_quota_error(exc: Exception) -> bool:
    msg       = str(exc).lower()
    type_name = type(exc).__name__.lower()
    return any(s in msg or s in type_name for s in _FALLBACK_SIGNALS)


def _make_provider(key: str):
    from src.llm.openai_provider import OpenAIProvider
    from src.llm.gemini_provider  import GeminiProvider
    from src.llm.groq_provider    import GroqProvider
    registry = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "groq":   GroqProvider,
    }
    if key not in registry:
        raise ValueError(f"Unknown provider '{key}'. Available: {list(registry.keys())}")
    provider = registry[key]()
    logger.info("Provider instantiated: %s", provider.provider_name)
    return provider


def _get_chat_provider():
    global _chat_provider_cache
    if _chat_provider_cache is None:
        _chat_provider_cache = _make_provider(settings.LLM_PROVIDER)
    return _chat_provider_cache


def _get_fallback_provider():
    """Second provider — Groq (when primary is OpenAI)"""
    global _fallback_provider_cache
    if _fallback_provider_cache is None:
        _fallback_provider_cache = _make_provider("groq")
    return _fallback_provider_cache


def _get_fallback2_provider():
    """Third provider — Gemini (final backup)"""
    global _fallback2_provider_cache
    if _fallback2_provider_cache is None:
        _fallback2_provider_cache = _make_provider("gemini")
    return _fallback2_provider_cache


def _get_embedding_provider():
    global _embedding_provider_cache
    if _embedding_provider_cache is None:
        _embedding_provider_cache = _make_provider(settings.EMBEDDING_PROVIDER)
    return _embedding_provider_cache


def clear_provider_cache() -> None:
    global _chat_provider_cache, _fallback_provider_cache
    global _fallback2_provider_cache, _embedding_provider_cache
    _chat_provider_cache      = None
    _fallback_provider_cache  = None
    _fallback2_provider_cache = None
    _embedding_provider_cache = None
    logger.info("LLM provider cache cleared.")


def invoke_with_fallback(messages: list) -> str:
    """
    Invoke LLM with automatic 3-tier fallback:
    Groq → OpenAI → Gemini

    Each provider is tried in order. If quota/rate limit is hit,
    the next provider is tried automatically. All fallbacks are
    logged as warnings so you can see them in LangSmith.
    """
    providers_to_try = []

    # Fallback chain: OpenAI (primary) → Groq → Gemini
    # Order chosen because:
    # - OpenAI: most reliable, best quality
    # - Groq: fastest, free tier, good fallback
    # - Gemini: final backup
    primary = settings.LLM_PROVIDER
    if primary == "openai":
        providers_to_try = [
            ("openai", _get_chat_provider),
            ("groq",   _get_fallback_provider),
            ("gemini", _get_fallback2_provider),
        ]
    elif primary == "groq":
        providers_to_try = [
            ("groq",   _get_chat_provider),
            ("openai", _get_fallback_provider),
            ("gemini", _get_fallback2_provider),
        ]
    else:  # gemini
        providers_to_try = [
            ("gemini", _get_chat_provider),
            ("openai", _get_fallback_provider),
            ("groq",   _get_fallback2_provider),
        ]

    last_exc = None
    for provider_name, get_provider_fn in providers_to_try:
        try:
            llm      = get_provider_fn().get_chat_model()
            response = llm.invoke(messages)
            if provider_name != primary:
                logger.info("✅ %s fallback succeeded.", provider_name)
            return response.content.strip()
        except Exception as exc:
            last_exc = exc
            if _is_quota_error(exc):
                logger.warning(
                    "⚠️  %s quota/rate error: %s — trying next provider.",
                    provider_name, str(exc)[:120],
                )
                continue
            else:
                # Non-quota error (bad API key, network, etc.) — raise immediately
                raise

    # All providers exhausted
    raise RuntimeError(
        f"All LLM providers failed (tried: {[p for p, _ in providers_to_try]}).\n"
        f"Last error: {last_exc}"
    ) from last_exc


def get_embeddings() -> Embeddings:
    """Return the configured embedding model."""
    return _get_embedding_provider().get_embeddings()


def get_chat_model() -> BaseChatModel:
    """Return the primary chat model."""
    return _get_chat_provider().get_chat_model()
