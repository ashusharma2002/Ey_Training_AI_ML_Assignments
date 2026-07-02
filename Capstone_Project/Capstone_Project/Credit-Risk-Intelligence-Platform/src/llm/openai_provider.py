# src/llm/openai_provider.py
from __future__ import annotations
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from config.settings import settings
from src.llm.base_provider import BaseLLMProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "openai"

    def get_chat_model(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not set in .env\n"
                "Get a key at: https://platform.openai.com/api-keys"
            )
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )

    def get_embeddings(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not set in .env\n"
                "Embeddings require OpenAI. Get a key at: https://platform.openai.com/api-keys"
            )

        kwargs = {
            "model": settings.OPENAI_EMBEDDING_MODEL,
            "openai_api_key": settings.OPENAI_API_KEY,
        }

        # text-embedding-3-* models support OpenAI's native dimension
        # reduction feature — lets us match whatever dimension your
        # Pinecone index was actually created with (e.g. 1024) instead
        # of forcing the model's default 1536. Older models (ada-002)
        # don't support this param, so only apply it for v3 models.
        if "text-embedding-3" in settings.OPENAI_EMBEDDING_MODEL:
            kwargs["dimensions"] = settings.OPENAI_EMBEDDING_DIMENSIONS
            logger.info(
                "Using OpenAI embeddings with dimensions=%d to match vector store.",
                settings.OPENAI_EMBEDDING_DIMENSIONS,
            )

        return OpenAIEmbeddings(**kwargs)
