from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings


@lru_cache(maxsize=4)
def _load_model(model_name: str, api_key: str) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=model_name,
        api_key=api_key,
        tiktoken_enabled=False,
        check_embedding_ctx_length=False,
    )


class MiniLMEmbeddings(Embeddings):
    def __init__(self, model_name: str, api_key: str):
        self.model = _load_model(model_name, api_key)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.model.embed_query(text)
