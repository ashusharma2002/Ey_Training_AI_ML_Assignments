# src/llm/openai_provider.py
# ============================================================
# OpenAI LLM Provider — wraps langchain-openai.
# ============================================================

from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from config.settings import settings
from src.llm.base_provider import BaseLLMProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """LLM provider backed by OpenAI's API."""

    def get_chat_model(self) -> BaseChatModel:
        logger.debug("Initialising OpenAI chat model: %s", settings.OPENAI_MODEL)
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY,
        )

    def get_embeddings(self) -> Embeddings:
        logger.debug(
            "Initialising OpenAI embeddings: %s", settings.OPENAI_EMBEDDING_MODEL
        )
        return OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )

    @property
    def provider_name(self) -> str:
        return "OpenAI"
