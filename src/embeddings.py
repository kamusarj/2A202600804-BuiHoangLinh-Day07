from __future__ import annotations

import hashlib
import math
import os

LOCAL_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENROUTER_EMBEDDING_MODEL = "openai/text-embedding-3-small"
EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"


class MockEmbedder:
    """Deterministic embedding backend used by tests and default classroom runs."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim
        self._backend_name = "mock embeddings fallback"

    def __call__(self, text: str) -> list[float]:
        digest = hashlib.md5(text.encode()).hexdigest()
        seed = int(digest, 16)
        vector = []
        for _ in range(self.dim):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            vector.append((seed / 0xFFFFFFFF) * 2 - 1)
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class LocalEmbedder:
    """Sentence Transformers-backed local embedder."""

    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._backend_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, text: str) -> list[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return [float(value) for value in embedding]


class OpenAIEmbedder:
    """OpenAI / OpenRouter embeddings API-backed embedder.

    Uses OpenRouter if OPENROUTER_API_KEY is set, otherwise uses OpenAI.
    """

    def __init__(self, model_name: str | None = None) -> None:
        from openai import OpenAI

        openai_api_key = os.getenv("OPENAI_API_KEY")
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

        if openrouter_api_key:
            self._backend_name = f"openrouter/{model_name or OPENROUTER_EMBEDDING_MODEL}"
            self.model_name = model_name or OPENROUTER_EMBEDDING_MODEL
            self.client = OpenAI(
                api_key=openrouter_api_key,
                base_url=openrouter_base_url,
            )
        else:
            self._backend_name = model_name or OPENAI_EMBEDDING_MODEL
            self.model_name = model_name or OPENAI_EMBEDDING_MODEL
            self.client = OpenAI(api_key=openai_api_key)

    def __call__(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model_name, input=text)
        return [float(value) for value in response.data[0].embedding]


_mock_embed = MockEmbedder()
