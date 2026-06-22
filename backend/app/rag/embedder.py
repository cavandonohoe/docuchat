"""Embedding client.

Wraps the OpenAI embeddings API behind a narrow protocol so tests can swap
in a deterministic fake.
"""

from __future__ import annotations

import logging
from typing import Protocol

from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def embed_one(self, text: str) -> list[float]: ...


class OpenAIEmbedder:
    def __init__(self, client: OpenAI | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self._client = client or OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self._model = model or settings.embedding_model

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        reraise=True,
    )
    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            resp = self._client.embeddings.create(model=self._model, input=texts)
        except Exception as exc:  # network or auth failures
            logger.exception("Embedding request failed")
            raise EmbeddingError(str(exc)) from exc
        return [d.embedding for d in resp.data]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]
