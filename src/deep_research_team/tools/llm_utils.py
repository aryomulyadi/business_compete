import asyncio
import os
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
    """Remove cache_breakpoint key from every message (some providers don't support it)."""
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


PRIMARY_MODEL = "openai/mimo-v2.5-pro"
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


class MimoDirect:
    """Direct Mimo API caller — bypasses LiteLLM to avoid unsupported params."""

    _SAFE_KEYS = frozenset({
        "temperature", "max_tokens", "top_p",
        "stream", "stop", "frequency_penalty", "presence_penalty",
        "response_format", "n",
    })

    def __init__(self, model: str = "mimo-v2.5-pro", max_tokens: int = 8192) -> None:
        import openai as _openai

        self.model = model
        self._max_tokens = max_tokens
        api_key = os.getenv("MIMO_API_KEY", "")
        base_url = "https://api.xiaomimimo.com/v1"
        self._client = _openai.OpenAI(api_key=api_key, base_url=base_url)
        self._aclient = _openai.AsyncOpenAI(api_key=api_key, base_url=base_url)

    def _build_kwargs(self, kwargs: dict) -> dict:
        return {k: v for k, v in kwargs.items() if k in self._SAFE_KEYS}

    def call(self, messages: Any, **kwargs: Any) -> str:
        safe = self._build_kwargs(kwargs)
        safe.setdefault("max_tokens", self._max_tokens)
        response = self._client.chat.completions.create(
            model=self.model, messages=messages, **safe,
        )
        content = response.choices[0].message.content
        if not content:
            import sys as _sys
            print(
                f"[MimoDirect] empty content (finish={response.choices[0].finish_reason}, "
                f"id={response.id}, model={response.model})",
                file=_sys.stderr,
            )
            return (
                f"[Mimo API returned empty response (finish_reason="
                f"{response.choices[0].finish_reason}, id={response.id})]"
            )
        return content

    async def acall(self, messages: Any, **kwargs: Any) -> str:
        safe = self._build_kwargs(kwargs)
        safe.setdefault("max_tokens", self._max_tokens)
        response = await self._aclient.chat.completions.create(
            model=self.model, messages=messages, **safe,
        )
        content = response.choices[0].message.content
        if not content:
            import sys as _sys
            print(
                f"[MimoDirect] empty content (finish={response.choices[0].finish_reason}, "
                f"id={response.id}, model={response.model})",
                file=_sys.stderr,
            )
            return (
                f"[Mimo API returned empty response (finish_reason="
                f"{response.choices[0].finish_reason}, id={response.id})]"
            )
        return content


class RetryableLLM(BaseLLM):
    """BaseLLM subclass with automatic retry (exponential backoff) and fallback model."""

    primary_model: str = PRIMARY_MODEL
    fallback_model: str = FALLBACK_MODEL

    _llm: Any = PrivateAttr()

    def __init__(self, **kwargs: Any) -> None:
        model = kwargs.pop("model", PRIMARY_MODEL)
        max_tokens = kwargs.pop("max_tokens", None)
        provider = model.split("/")[0] if "/" in model else "openai"
        super().__init__(
            llm_type=provider,
            model=model,
            **kwargs,
        )
        if "mimo" in model.lower():
            raw_model = model.split("/", 1)[1] if "/" in model else model
            mimo_kwargs = {"model": raw_model}
            if max_tokens is not None:
                mimo_kwargs["max_tokens"] = max_tokens
            self._llm = MimoDirect(**mimo_kwargs)
        else:
            self._llm = LLM(model=model)

    def call(
        self,
        messages: str | list[LLMMessage],
        **kwargs: Any,
    ) -> Any:
        last_error = None
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


_PROVIDER_MAP = {
    "deepseek": "deepseek/deepseek-chat",
    "groq": "groq/llama-3.3-70b-versatile",
    "gemini": "gemini/gemini-2.5-flash",
    "openai": "gpt-4o",
    "openai-mini": "gpt-4o-mini",
    "mimo": "openai/mimo-v2.5-pro",
}


def get_llm(max_tokens: int | None = None) -> BaseLLM:
    """Create a RetryableLLM instance based on LLM_PROVIDER env var."""
    provider = os.getenv("LLM_PROVIDER", "mimo").lower()
    model = _PROVIDER_MAP.get(provider, PRIMARY_MODEL)
    kwargs: dict = {"model": model}
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    return RetryableLLM(**kwargs)
