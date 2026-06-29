# src/llm/gemini_provider.py
# ============================================================
# Google Gemini LLM Provider — wraps langchain-google-genai.
# ============================================================

from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from config.settings import settings
from src.llm.base_provider import BaseLLMProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseLLMProvider):
    """LLM provider backed by Google Gemini."""

    def get_chat_model(self) -> BaseChatModel:
        logger.debug("Initialising Gemini chat model: %s", settings.GEMINI_MODEL)
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            temperature=settings.GEMINI_TEMPERATURE,
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
            google_api_key=settings.GEMINI_API_KEY,
            convert_system_message_to_human=True,
        )

    def get_embeddings(self) -> Embeddings:
        logger.debug(
            "Initialising Gemini embeddings: %s", settings.GEMINI_EMBEDDING_MODEL
        )
        return GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
        )

    @property
    def provider_name(self) -> str:
        return "Google Gemini"
