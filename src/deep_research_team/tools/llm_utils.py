from __future__ import annotations

import asyncio
import hashlib
import json
import os
import random
import re
import time
from typing import TYPE_CHECKING, Any

import litellm
from litellm.exceptions import APIConnectionError, InternalServerError, RateLimitError, ServiceUnavailableError
from crewai import LLM
from crewai.llms.base_llm import BaseLLM
from crewai.utilities.types import LLMMessage
from pydantic import BaseModel, PrivateAttr

from deep_research_team.settings import setup_logging

if TYPE_CHECKING:
    from crewai.agents.agent_builder.base_agent import BaseAgent
    from crewai.task import Task
    from crewai.tools.base_tool import BaseTool

logger = setup_logging(__name__)

litellm.drop_params = True


def _strip_cache_breakpoint(messages: list[dict]) -> list[dict]:
    """Return messages with cache_breakpoint key removed (some providers don't support it)."""
    return [
        {k: v for k, v in msg.items() if k != "cache_breakpoint"}
        if isinstance(msg, dict) else msg
        for msg in messages
    ]


_llm_response_cache: dict[str, str] = {}


def clear_llm_cache() -> None:
    _llm_response_cache.clear()


def _llm_cache_key(messages: str | list[LLMMessage], model: str, temperature: float) -> str:
    raw = json.dumps({"model": model, "temperature": temperature, "messages": messages}, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


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


PRIMARY_MODEL = "mimo-v2.5-pro"
FALLBACK_MODEL = "groq/llama-3.3-70b-versatile"
OMNIROUTE_DEFAULT_MODEL = "auto"
MIMO_DEFAULT_BASE_URL = "https://api.xiaomimimo.com/v1"
MIMO_DEFAULT_THINKING_TYPE = "disabled"
MAX_RETRIES = 3
BASE_DELAY = 2.0

RETRYABLE_CODES = {429, 503}


def _is_retryable(error: Exception) -> bool:
    if isinstance(error, (ValueError, RateLimitError, ServiceUnavailableError, InternalServerError, APIConnectionError)):
        return True
    error_str = str(error).lower()
    for code in RETRYABLE_CODES:
        if str(code) in error_str:
            return True
    if "timed out" in error_str or "timeout" in error_str:
        return True
    return False


def _parse_retry_delay(error: Exception, attempt: int) -> float:
    delay = BASE_DELAY * (2 ** attempt)
    m = re.search(r"try again in ([\d.]+)s", str(error))
    if m:
        delay = max(delay, float(m.group(1)) + 1)
    return delay + random.uniform(0, 1)


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
        "temperature", "max_completion_tokens", "top_p",
        "stream", "stop", "frequency_penalty", "presence_penalty",
        "response_format", "n", "tools", "tool_choice", "parallel_tool_calls",
    })

    def __init__(self, model: str = PRIMARY_MODEL, max_tokens: int = 8192) -> None:
        self.model = model
        self._max_tokens = max_tokens
        self._client: Any = None
        self._aclient: Any = None
        self._base_url = _env_value("MIMO_BASE_URL", MIMO_DEFAULT_BASE_URL)
        self._thinking_type = _env_value("MIMO_THINKING", MIMO_DEFAULT_THINKING_TYPE).lower()

    def _get_client(self) -> Any:
        if self._client is None:
            import openai as _openai
            api_key = os.getenv("MIMO_API_KEY", "")
            self._client = _openai.OpenAI(api_key=api_key, base_url=self._base_url, timeout=120)
        return self._client

    def _get_aclient(self) -> Any:
        if self._aclient is None:
            import openai as _openai
            api_key = os.getenv("MIMO_API_KEY", "")
            self._aclient = _openai.AsyncOpenAI(api_key=api_key, base_url=self._base_url, timeout=120)
        return self._aclient

    def _build_kwargs(self, call_options: dict[str, Any]) -> dict[str, Any]:
        safe = {k: v for k, v in call_options.items() if k in self._SAFE_KEYS}
        if "max_tokens" in call_options and "max_completion_tokens" not in safe:
            safe["max_completion_tokens"] = call_options["max_tokens"]
        extra_body = dict(call_options["extra_body"]) if isinstance(call_options.get("extra_body"), dict) else {}
        thinking = call_options.get("thinking")
        if self._thinking_type in {"enabled", "disabled"}:
            thinking = thinking or {"type": self._thinking_type}
        if thinking is not None:
            extra_body["thinking"] = thinking
        if extra_body:
            safe["extra_body"] = extra_body
        return safe

    def call(self, messages: Any, **call_options: Any) -> str:
        safe = self._build_kwargs(call_options)
        safe.setdefault("max_completion_tokens", self._max_tokens)
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

    async def acall(self, messages: Any, **call_options: Any) -> str:
        safe = self._build_kwargs(call_options)
        safe.setdefault("max_completion_tokens", self._max_tokens)
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
    @property
    def supports_function_calling(self) -> bool:
        return False

    _llm: Any = PrivateAttr()
    _llm_kwargs: dict[str, Any] = PrivateAttr(default_factory=dict)
    _fallback_enabled: bool = PrivateAttr(default=True)
    _max_tokens: int | None = PrivateAttr(default=None)
    _temperature: float = PrivateAttr(default=0.0)

    def __init__(self, **config: Any) -> None:
        model = config.pop("model", PRIMARY_MODEL)
        max_tokens = config.pop("max_tokens", None)
        base_url = config.pop("base_url", None)
        api_key = config.pop("api_key", None)
        fallback_enabled = config.pop("fallback_enabled", True)
        temperature = config.pop("temperature", 0.0)
        is_mimo_model = "mimo" in model.lower() and not base_url
        provider = "mimo" if is_mimo_model else model.split("/")[0] if "/" in model else "openai"
        super().__init__(
            llm_type=provider,
            model=model,
            temperature=temperature,
            **config,
        )
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._fallback_enabled = fallback_enabled
        if base_url:
            self._llm_kwargs["base_url"] = base_url
        if api_key is not None:
            self._llm_kwargs["api_key"] = api_key
        if max_tokens is not None:
            self._llm_kwargs["max_tokens"] = max_tokens

        if is_mimo_model:
            raw_model = model.removeprefix("openai/")
            mimo_kwargs = {"model": raw_model}
            if max_tokens is not None:
                mimo_kwargs["max_tokens"] = max_tokens
            self._llm = MimoDirect(**mimo_kwargs)
        else:
            self._llm = LLM(model=model, temperature=temperature, **self._llm_kwargs)

    def call(
        self,
        messages: str | list[LLMMessage],
        tools: list[dict[str, BaseTool]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        from_task: Task | None = None,
        from_agent: BaseAgent | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> str | Any:
        last_error = None
        fallback = self.fallback_model

        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0 and not self._fallback_enabled:
                    logger.info("Retry attempt %d - retrying model: %s", attempt, self.model)
                elif attempt > 0:
                    logger.info("Retry attempt %d — switching to fallback: %s", attempt, fallback)
                    fb_kwargs = {"model": fallback}
                    if self._max_tokens is not None:
                        fb_kwargs["max_tokens"] = self._max_tokens
                    self._llm = LLM(**fb_kwargs)
                    self.model = self._llm.model
                llm_kwargs: dict[str, Any] = dict(
                    messages=messages,
                    tools=tools,
                    callbacks=callbacks,
                    available_functions=available_functions,
                    from_task=from_task,
                    from_agent=from_agent,
                    response_model=response_model,
                )
                if isinstance(self._llm, MimoDirect):
                    llm_kwargs["temperature"] = self._temperature
                ck = _llm_cache_key(messages, self.model, self._temperature)
                if ck in _llm_response_cache:
                    logger.debug("LLM cache hit for key=%s", ck[:16])
                    return _llm_response_cache[ck]
                result = self._llm.call(**llm_kwargs)
                if isinstance(result, str):
                    _llm_response_cache[ck] = result
                return result
            except Exception as e:
                last_error = e
                if not _is_retryable(e):
                    raise
                delay = _parse_retry_delay(e, attempt)
                logger.warning(
                    "Attempt %d failed (%s: %s), retrying in %.1fs",
                    attempt, type(e).__name__, e, delay,
                )
                time.sleep(delay)

        raise last_error  # type: ignore[misc]

    async def acall(
        self,
        messages: str | list[LLMMessage],
        tools: list[dict[str, BaseTool]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        from_task: Task | None = None,
        from_agent: BaseAgent | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> str | Any:
        last_error = None
        fallback = self.fallback_model

        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0 and not self._fallback_enabled:
                    logger.info("Retry attempt %d - retrying model: %s", attempt, self.model)
                elif attempt > 0:
                    logger.info("Retry attempt %d — switching to fallback: %s", attempt, fallback)
                    fb_kwargs = {"model": fallback}
                    if self._max_tokens is not None:
                        fb_kwargs["max_tokens"] = self._max_tokens
                    self._llm = LLM(**fb_kwargs)
                    self.model = self._llm.model
                llm_kwargs: dict[str, Any] = dict(
                    messages=messages,
                    tools=tools,
                    callbacks=callbacks,
                    available_functions=available_functions,
                    from_task=from_task,
                    from_agent=from_agent,
                    response_model=response_model,
                )
                if isinstance(self._llm, MimoDirect):
                    llm_kwargs["temperature"] = self._temperature
                ck = _llm_cache_key(messages, self.model, self._temperature)
                if ck in _llm_response_cache:
                    logger.debug("LLM cache hit for key=%s", ck[:16])
                    return _llm_response_cache[ck]
                result = await self._llm.acall(**llm_kwargs)
                if isinstance(result, str):
                    _llm_response_cache[ck] = result
                return result
            except Exception as e:
                last_error = e
                if not _is_retryable(e):
                    raise
                delay = _parse_retry_delay(e, attempt)
                logger.warning(
                    "Attempt %d failed (%s: %s), retrying in %.1fs (acall)",
                    attempt, type(e).__name__, e, delay,
                )
                await asyncio.sleep(delay)

        raise last_error  # type: ignore[misc]


_PROVIDER_MAP = {
    "deepseek": "deepseek/deepseek-chat",
    "groq": "groq/llama-3.3-70b-versatile",
    "gemini": "gemini/gemini-3.1-flash-lite-preview",
    "openai": "gpt-4o",
    "openai-mini": "gpt-4o-mini",
    "mimo": PRIMARY_MODEL,
}


def get_llm(max_tokens: int | None = None) -> BaseLLM:
    """Create a RetryableLLM instance based on LLM_PROVIDER env var."""
    provider = os.getenv("LLM_PROVIDER", "mimo").lower()
    if provider == "omniroute":
        omniroute_kwargs: dict[str, Any] = {
            "model": _openai_compatible_model(_env_value("OMNIROUTE_MODEL", OMNIROUTE_DEFAULT_MODEL)),
            "base_url": _required_env_value("OMNIROUTE_BASE_URL"),
            "api_key": _env_value("OMNIROUTE_API_KEY", "omniroute-local"),
            "fallback_enabled": False,
        }
        if max_tokens is not None:
            omniroute_kwargs["max_tokens"] = max_tokens
        return RetryableLLM(**omniroute_kwargs)

    model = _PROVIDER_MAP.get(provider, PRIMARY_MODEL)
    provider_kwargs: dict[str, Any] = {"model": model}
    if max_tokens is not None:
        provider_kwargs["max_tokens"] = max_tokens
    return RetryableLLM(**provider_kwargs)
