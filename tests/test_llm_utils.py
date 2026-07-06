import os
from unittest.mock import patch

import pytest
from litellm.exceptions import RateLimitError, ServiceUnavailableError

try:
    from deep_research_team.tools.llm_utils import (
        MimoDirect,
        RetryableLLM,
        _is_retryable,
        get_llm,
    )
except ModuleNotFoundError:
    pytest.skip("Missing dependencies (litellm, crewai)", allow_module_level=True)


class TestIsRetryable:
    def test_429_error(self) -> None:
        assert _is_retryable(Exception("HTTP 429 Too Many Requests"))

    def test_503_error(self) -> None:
        assert _is_retryable(Exception("HTTP 503 Service Unavailable"))

    def test_non_retryable_error(self) -> None:
        assert not _is_retryable(Exception("HTTP 400 Bad Request"))

    def test_unknown_error(self) -> None:
        assert not _is_retryable(Exception("connection refused"))

    def test_value_error_retryable(self) -> None:
        assert _is_retryable(ValueError("Empty response from Mimo API"))

    def test_rate_limit_error_via_isinstance(self) -> None:
        assert _is_retryable(RateLimitError(
            "Rate limit exceeded for model llama-3.1-8b-instant",
            "groq", "llama-3.1-8b-instant",
        ))

    def test_service_unavailable_via_isinstance(self) -> None:
        assert _is_retryable(ServiceUnavailableError(
            "Service is temporarily unavailable",
            "groq", "llama-3.1-8b-instant",
        ))


class TestMimoDirect:
    def test_init_sets_model_and_max_tokens(self) -> None:
        mimo = MimoDirect(model="mimo-test", max_tokens=4096)
        assert mimo.model == "mimo-test"
        assert mimo._max_tokens == 4096

    def test_build_kwargs_filters_unsafe_keys(self) -> None:
        mimo = MimoDirect()
        kwargs = mimo._build_kwargs({
            "temperature": 0.7,
            "max_tokens": 100,
            "bad_param": "should be filtered",
            "another_bad": 123,
        })
        assert "temperature" in kwargs
        assert "max_tokens" in kwargs
        assert "bad_param" not in kwargs
        assert "another_bad" not in kwargs

    def test_build_kwargs_sets_defaults(self) -> None:
        mimo = MimoDirect(max_tokens=2048)
        kwargs = mimo._build_kwargs({})
        assert "max_tokens" not in kwargs  # doesn't mutate input
        safe = mimo._build_kwargs(kwargs)
        safe.setdefault("max_tokens", mimo._max_tokens)
        kwargs2 = mimo._build_kwargs({})
        kwargs2.setdefault("max_tokens", mimo._max_tokens)
        assert kwargs2["max_tokens"] == 2048


class TestRetryableLLM:
    def test_init_with_mimo_model(self) -> None:
        llm = RetryableLLM(model="openai/mimo-test")
        assert hasattr(llm, "_llm")

    def test_init_with_groq_model(self) -> None:
        llm = RetryableLLM(model="groq/llama-3.1-8b-instant")
        assert hasattr(llm, "_llm")

    def test_get_llm_default_provider(self) -> None:
        if "LLM_PROVIDER" in os.environ:
            del os.environ["LLM_PROVIDER"]
        llm = get_llm(max_tokens=4096)
        assert isinstance(llm, RetryableLLM)

    def test_get_llm_with_provider(self) -> None:
        os.environ["LLM_PROVIDER"] = "groq"
        llm = get_llm(max_tokens=2048)
        assert isinstance(llm, RetryableLLM)
        assert "groq/" in llm.model

    def test_get_llm_with_unknown_provider(self) -> None:
        os.environ["LLM_PROVIDER"] = "nonexistent"
        llm = get_llm()
        assert isinstance(llm, RetryableLLM)

    def test_get_llm_no_max_tokens(self) -> None:
        os.environ["LLM_PROVIDER"] = "groq"
        llm = get_llm()
        assert isinstance(llm, RetryableLLM)
