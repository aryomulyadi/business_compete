import asyncio
import os
import random
import time
from typing import Any

import litellm
from litellm.exceptions import APIConnectionError, InternalServerError, RateLimitError, ServiceUnavailableError
from crewai import LLM
from crewai.llms.base_llm import BaseLLM
from crewai.utilities.types import LLMMessage
from pydantic import PrivateAttr

from deep_research_team.settings import setup_logging

logger = setup_logging(__name__)

litellm.drop_params = True


def _strip_cache_breakpoint(messages: list[dict]) -> list[dict]:
    """Return messages with cache_breakpoint key removed (some providers don't support it)."""
    return [
        {k: v for k, v in msg.items() if k != "cache_breakpoint"}
        if isinstance(msg, dict) else msg
        for msg in messages
    ]


_original_completion = litellm.completion
_original_acompletion = litellm.acompletion


def _patched_completion(*args: Any, **kwargs: Any) -> Any:
    if "messages" in kwargs:
        kwargs["messages"] = _strip_cache_breakpoint(kwargs["messages"])
    return _original_completion(*args, **kwargs)


async def _patched_acompletion(*args: Any, **kwargs: Any) -> Any:
    if "messages" in kwargs:
        kwargs["messages"] = _strip_cache_breakpoint(kwargs["messages"])
    return await _original_acompletion(*args, **kwargs)


litellm.completion = _patched_completion
litellm.acompletion = _patched_acompletion


PRIMARY_MODEL = "openai/mimo-v2.5-pro"
FALLBACK_MODEL = "groq/llama-3.1-8b-instant"
OMNIROUTE_DEFAULT_MODEL = "auto"
MAX_RETRIES = 3
BASE_DELAY = 2.0

RETRYABLE_CODES = {429, 503}


def _is_retryable(error: Exception) -> bool:
    if isinstance(error, (ValueError, RateLimitError, ServiceUnavailableError, InternalServerError, APIConnectionError)):
        return True
    error_str = str(error)
    for code in RETRYABLE_CODES:
        if str(code) in error_str:
            return True
    return False


def _env_value(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    return value or default


def _openai_compatible_model(model: str) -> str:
    if model.startswith("openai/"):
        return model
    return f"openai/{model}"


def _required_env_value(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required when LLM_PROVIDER=omniroute")
    return value


class MimoDirect:
    """Direct Mimo API caller — bypasses LiteLLM to avoid unsupported params."""

    _SAFE_KEYS = frozenset({
        "temperature", "max_tokens", "top_p",
        "stream", "stop", "frequency_penalty", "presence_penalty",
        "response_format", "n",
    })

    def __init__(self, model: str = "mimo-v2.5-pro", max_tokens: int = 8192) -> None:
        self.model = model
        self._max_tokens = max_tokens
        self._client: Any = None
        self._aclient: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import openai as _openai
            api_key = os.getenv("MIMO_API_KEY", "")
            base_url = "https://api.xiaomimimo.com/v1"
            self._client = _openai.OpenAI(api_key=api_key, base_url=base_url)
        return self._client

    def _get_aclient(self) -> Any:
        if self._aclient is None:
            import openai as _openai
            api_key = os.getenv("MIMO_API_KEY", "")
            base_url = "https://api.xiaomimimo.com/v1"
            self._aclient = _openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        return self._aclient

    def _build_kwargs(self, kwargs: dict) -> dict:
        return {k: v for k, v in kwargs.items() if k in self._SAFE_KEYS}

    def call(self, messages: Any, **kwargs: Any) -> str:
        safe = self._build_kwargs(kwargs)
        safe.setdefault("max_tokens", self._max_tokens)
        response = self._get_client().chat.completions.create(
            model=self.model, messages=messages, **safe,
        )
        content = response.choices[0].message.content
        if not content:
            logger.warning(
                "MimoDirect empty content (finish=%s, id=%s, model=%s) — raising ValueError",
                response.choices[0].finish_reason,
                response.id,
                response.model,
            )
            raise ValueError(
                f"Mimo API returned empty content (finish_reason="
                f"{response.choices[0].finish_reason}, id={response.id})"
            )
        return content

    async def acall(self, messages: Any, **kwargs: Any) -> str:
        safe = self._build_kwargs(kwargs)
        safe.setdefault("max_tokens", self._max_tokens)
        response = await self._get_aclient().chat.completions.create(
            model=self.model, messages=messages, **safe,
        )
        content = response.choices[0].message.content
        if not content:
            logger.warning(
                "MimoDirect empty content (finish=%s, id=%s, model=%s) — raising ValueError",
                response.choices[0].finish_reason,
                response.id,
                response.model,
            )
            raise ValueError(
                f"Mimo API returned empty content (finish_reason="
                f"{response.choices[0].finish_reason}, id={response.id})"
            )
        return content


class RetryableLLM(BaseLLM):
    """BaseLLM subclass with automatic retry (exponential backoff) and fallback model."""

    primary_model: str = PRIMARY_MODEL
    fallback_model: str = FALLBACK_MODEL

    _llm: Any = PrivateAttr()
    _llm_kwargs: dict[str, Any] = PrivateAttr(default_factory=dict)
    _fallback_enabled: bool = PrivateAttr(default=True)
    _max_tokens: int | None = PrivateAttr(default=None)

    def __init__(self, **kwargs: Any) -> None:
        model = kwargs.pop("model", PRIMARY_MODEL)
        max_tokens = kwargs.pop("max_tokens", None)
        base_url = kwargs.pop("base_url", None)
        api_key = kwargs.pop("api_key", None)
        fallback_enabled = kwargs.pop("fallback_enabled", True)
        provider = model.split("/")[0] if "/" in model else "openai"
        super().__init__(
            llm_type=provider,
            model=model,
            **kwargs,
        )
        self._max_tokens = max_tokens
        self._fallback_enabled = fallback_enabled
        if base_url:
            self._llm_kwargs["base_url"] = base_url
        if api_key is not None:
            self._llm_kwargs["api_key"] = api_key
        if max_tokens is not None:
            self._llm_kwargs["max_tokens"] = max_tokens

        if "mimo" in model.lower() and not base_url:
            raw_model = model.split("/", 1)[1] if "/" in model else model
            mimo_kwargs = {"model": raw_model}
            if max_tokens is not None:
                mimo_kwargs["max_tokens"] = max_tokens
            self._llm = MimoDirect(**mimo_kwargs)
        else:
            self._llm = LLM(model=model, **self._llm_kwargs)

    def call(
        self,
        messages: str | list[LLMMessage],
        **kwargs: Any,
    ) -> Any:
        last_error = None
        fallback = self.fallback_model

        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0 and not self._fallback_enabled:
                    logger.info("Retry attempt %d - retrying model: %s", attempt, self.model)
                elif attempt > 0:
                    logger.info("Retry attempt %d — switching to fallback: %s", attempt, fallback)
                    self._llm = LLM(model=fallback)
                    self.model = self._llm.model
                return self._llm.call(messages, **kwargs)
            except Exception as e:
                last_error = e
                if not _is_retryable(e):
                    raise
                delay = BASE_DELAY * (2**attempt) + random.uniform(0, 1)
                logger.warning(
                    "Attempt %d failed (%s: %s), retrying in %.1fs",
                    attempt, type(e).__name__, e, delay,
                )
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
                if attempt > 0 and not self._fallback_enabled:
                    logger.info("Retry attempt %d - retrying model: %s", attempt, self.model)
                elif attempt > 0:
                    logger.info("Retry attempt %d — switching to fallback: %s", attempt, fallback)
                    self._llm = LLM(model=fallback)
                    self.model = self._llm.model
                return await self._llm.acall(messages, **kwargs)
            except Exception as e:
                last_error = e
                if not _is_retryable(e):
                    raise
                delay = BASE_DELAY * (2**attempt) + random.uniform(0, 1)
                logger.warning(
                    "Attempt %d failed (%s: %s), retrying in %.1fs",
                    attempt, type(e).__name__, e, delay,
                )
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
    if provider == "omniroute":
        kwargs: dict = {
            "model": _openai_compatible_model(_env_value("OMNIROUTE_MODEL", OMNIROUTE_DEFAULT_MODEL)),
            "base_url": _required_env_value("OMNIROUTE_BASE_URL"),
            "api_key": _env_value("OMNIROUTE_API_KEY", "omniroute-local"),
            "fallback_enabled": False,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return RetryableLLM(**kwargs)

    model = _PROVIDER_MAP.get(provider, PRIMARY_MODEL)
    kwargs: dict = {"model": model}
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    return RetryableLLM(**kwargs)
