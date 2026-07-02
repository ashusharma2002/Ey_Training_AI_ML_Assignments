# src/llm/groq_provider.py
# ============================================================
# Groq LLM Provider
#
# Groq runs open-source models (Llama, Mixtral) on custom
# hardware — extremely fast (tokens/sec) and has a generous
# free tier with high rate limits.
#
# Why Groq as PRIMARY:
# - Free tier: 14,400 requests/day, 30 req/min per model
# - Speed: ~500 tokens/sec (10x faster than Gemini/OpenAI)
# - No credit card needed
# - Get free key at: https://console.groq.com
#
# Model used: llama-3.3-70b-versatile
# - 128k context window (handles large documents)
# - Strong reasoning and instruction following
# - No cost on free tier
# ============================================================
from __future__ import annotations
from langchain_groq import ChatGroq
from config.settings import settings
from src.llm.base_provider import BaseLLMProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GroqProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "groq"

    def get_chat_model(self):
        if not settings.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not set in .env\n"
                "Get a free key at: https://console.groq.com\n"
                "Free tier: 14,400 requests/day — no credit card needed"
            )
        return ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.1,
            max_tokens=4096,
        )

    def get_embeddings(self):
        # Groq does not provide embeddings — fall back to OpenAI embeddings
        # This is intentional: Groq is chat-only
        raise NotImplementedError(
            "Groq does not support embeddings. "
            "Use OpenAI or Gemini for embeddings."
        )
