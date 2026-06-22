"""Chat completion client."""

from __future__ import annotations

import logging
from typing import Protocol

from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.exceptions import GenerationError

logger = logging.getLogger(__name__)


class Generator(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


class OpenAIGenerator:
    def __init__(self, client: OpenAI | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self._client = client or OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self._model = model or settings.chat_model

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        reraise=True,
    )
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )
        except Exception as exc:
            logger.exception("Chat completion request failed")
            raise GenerationError(str(exc)) from exc
        content = resp.choices[0].message.content or ""
        return content.strip()
