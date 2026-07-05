import asyncio
import random
import time
from typing import Any

import litellm
from crewai import LLM
from crewai.llms.base_llm import BaseLLM
from crewai.utilities.types import LLMMessage
from pydantic import PrivateAttr

litellm.drop_params = True


def _strip_cache_breakpoint(messages: list[dict]) -> None:
    """Remove cache_breakpoint key from every message (Groq doesn't support it)."""
    for msg in messages:
        if isinstance(msg, dict):
            msg.pop("cache_breakpoint", None)


_original_completion = litellm.completion
_original_acompletion = litellm.acompletion


def _patched_completion(*args: Any, **kwargs: Any) -> Any:
    if "messages" in kwargs:
        _strip_cache_breakpoint(kwargs["messages"])
    return _original_completion(*args, **kwargs)


async def _patched_acompletion(*args: Any, **kwargs: Any) -> Any:
    if "messages" in kwargs:
        _strip_cache_breakpoint(kwargs["messages"])
    return await _original_acompletion(*args, **kwargs)


litellm.completion = _patched_completion
litellm.acompletion = _patched_acompletion


PRIMARY_MODEL = "groq/llama-3.3-70b-versatile"
FALLBACK_MODEL = "groq/llama-3.1-8b-instant"
MAX_RETRIES = 3
BASE_DELAY = 2.0

RETRYABLE_CODES = {429, 503}


def _is_retryable(error: Exception) -> bool:
    error_str = str(error)
    for code in RETRYABLE_CODES:
        if str(code) in error_str:
            return True
    return False


class RetryableLLM(BaseLLM):
    """BaseLLM subclass with automatic retry (exponential backoff) and fallback model."""

    primary_model: str = PRIMARY_MODEL
    fallback_model: str = FALLBACK_MODEL

    _llm: Any = PrivateAttr()

    def __init__(self, **kwargs: Any) -> None:
        model = kwargs.pop("model", PRIMARY_MODEL)
        model_clean = model.replace("groq/", "").replace("gemini/", "")
        super().__init__(
            llm_type="groq",
            model=model,
            provider="openai",
            **kwargs,
        )
        self._llm = LLM(model=model)

    def call(
        self,
        messages: str | list[LLMMessage],
        **kwargs: Any,
    ) -> Any:
        last_error = None
        primary = self.primary_model
        fallback = self.fallback_model

        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    self._llm = LLM(model=fallback)
                    self.model = self._llm.model
                return self._llm.call(messages, **kwargs)
            except Exception as e:
                last_error = e
                if not _is_retryable(e):
                    raise
                delay = BASE_DELAY * (2**attempt) + random.uniform(0, 1)
                time.sleep(delay)

        raise last_error  # type: ignore[misc]

    async def acall(
        self,
        messages: str | list[LLMMessage],
        **kwargs: Any,
    ) -> Any:
        last_error = None
        primary = self.primary_model
        fallback = self.fallback_model

        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    self._llm = LLM(model=fallback)
                    self.model = self._llm.model
                return await self._llm.acall(messages, **kwargs)
            except Exception as e:
                last_error = e
                if not _is_retryable(e):
                    raise
                delay = BASE_DELAY * (2**attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)

        raise last_error  # type: ignore[misc]


def get_llm() -> BaseLLM:
    """Create a RetryableLLM instance."""
    return RetryableLLM(model=PRIMARY_MODEL)
