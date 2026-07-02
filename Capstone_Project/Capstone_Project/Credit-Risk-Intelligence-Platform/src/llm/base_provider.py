# src/llm/base_provider.py
from __future__ import annotations
from abc import ABC, abstractmethod
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel


class BaseLLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def get_chat_model(self) -> BaseChatModel: ...

    @abstractmethod
    def get_embeddings(self) -> Embeddings: ...
