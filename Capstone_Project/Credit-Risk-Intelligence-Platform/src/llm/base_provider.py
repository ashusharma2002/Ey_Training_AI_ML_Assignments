# src/llm/base_provider.py
# ============================================================
# Abstract base class for all LLM providers.
# Adding a new provider (Claude, Azure OpenAI, Groq, etc.)
# requires only implementing this interface and registering
# it in llm_factory.py — zero changes elsewhere.
# ============================================================

from __future__ import annotations

from abc import ABC, abstractmethod

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel


class BaseLLMProvider(ABC):
    """Contract that every LLM provider must fulfil."""

    @abstractmethod
    def get_chat_model(self) -> BaseChatModel:
        """Return a LangChain-compatible chat model instance."""

    @abstractmethod
    def get_embeddings(self) -> Embeddings:
        """Return a LangChain-compatible embeddings instance."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier."""
