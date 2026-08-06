from __future__ import annotations

from functools import lru_cache
import hashlib
import math

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

    @staticmethod
    def _fallback_vector(text: str, dims: int = 384) -> list[float]:
        vector = [0.0] * dims
        tokens = text.lower().split()
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for i in range(0, 32, 4):
                slot = int.from_bytes(digest[i : i + 4], "little") % dims
                vector[slot] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        try:
            return self.model.embed_documents(texts)
        except Exception:
            return [self._fallback_vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        try:
            return self.model.embed_query(text)
        except Exception:
            return self._fallback_vector(text)
