import base64
import os
from unittest.mock import MagicMock, patch

import pytest

from deep_research_team.tools.image_generator import (
    _build_prompt,
    _try_cloudflare,
    _try_gemini,
    _validate_image_bytes,
    generate_logo_image,
)


class TestValidateImageBytes:
    def test_valid_size(self):
        assert _validate_image_bytes(b"x" * 1024) is None

    def test_exactly_max(self):
        assert _validate_image_bytes(b"x" * (5 * 1024 * 1024)) is None

    def test_too_large(self):
        err = _validate_image_bytes(b"x" * (5 * 1024 * 1024 + 1))
        assert err is not None
        assert "5MB" in err

    def test_empty(self):
        assert _validate_image_bytes(b"") is None


class TestBuildPrompt:
    def test_minimal(self):
        prompt = _build_prompt("Test Brand", {}, "Gaya modern minimalis.")
        assert "Test Brand" in prompt
        assert "1024x1024" in prompt
        assert "PNG" in prompt

    def test_all_fields(self):
        concept = {
            "meaning": "Makna test",
            "philosophy": "Filosofi test",
            "target_market": "Target test",
            "positioning": "Positioning test",
        }
        prompt = _build_prompt("Brand", concept, "Gaya elegan.")
        for v in concept.values():
            assert v in prompt

    def test_partial_fields(self):
        concept = {"meaning": "Hanya makna"}
        prompt = _build_prompt("Brand", concept, "Gaya.")
        assert "Hanya makna" in prompt
        assert "positio" not in prompt


class TestTryCloudflare:
    @patch("deep_research_team.tools.image_generator.requests.post")
    def test_success(self, mock_post):
        img_bytes = b"fake_png_data"
        mock_post.return_value = MagicMock(
            ok=True,
            json=lambda: {
                "success": True,
                "result": {"image": base64.b64encode(img_bytes).decode()},
                "errors": [],
            },
        )
        result = _try_cloudflare("test prompt", "fake-account-id", "fake-token")
        assert result == img_bytes

    @patch("deep_research_team.tools.image_generator.requests.post")
    def test_non_200(self, mock_post):
        mock_post.return_value = MagicMock(
            ok=False,
            json=lambda: {"success": False, "errors": [{"message": "Invalid auth"}]},
        )
        assert _try_cloudflare("test", "fake-account-id", "fake-token") is None

    @patch("deep_research_team.tools.image_generator.requests.post")
    def test_missing_image_field(self, mock_post):
        mock_post.return_value = MagicMock(
            ok=True,
            json=lambda: {"success": True, "result": {}, "errors": []},
        )
        assert _try_cloudflare("test", "fake-account-id", "fake-token") is None

    @patch("deep_research_team.tools.image_generator.requests.post")
    def test_invalid_base64(self, mock_post):
        mock_post.return_value = MagicMock(
            ok=True,
            json=lambda: {
                "success": True,
                "result": {"image": "not-base64!!!"},
                "errors": [],
            },
        )
        assert _try_cloudflare("test", "fake-account-id", "fake-token") is None

    @patch("deep_research_team.tools.image_generator.requests.post")
    def test_connection_error(self, mock_post):
        from requests.exceptions import ConnectionError

        mock_post.side_effect = ConnectionError("Connection refused")
        assert _try_cloudflare("test", "fake-account-id", "fake-token") is None


class TestTryGemini:
    @patch("deep_research_team.tools.image_generator.genai.Client")
    def test_success(self, mock_client_cls):
        img_bytes = b"fake_png"
        mock_part = MagicMock()
        mock_part.inline_data.mime_type = "image/png"
        mock_part.inline_data.data = img_bytes

        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]

        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            result = _try_gemini("test prompt")
        assert result == img_bytes

    @patch("deep_research_team.tools.image_generator.genai.Client")
    def test_no_image_in_response(self, mock_client_cls):
        mock_part = MagicMock()
        mock_part.text = "Here is a description but no image"
        del mock_part.inline_data

        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]

        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            assert _try_gemini("test") is None

    @patch("deep_research_team.tools.image_generator.genai.Client")
    def test_no_api_key(self, mock_client_cls):
        with patch.dict(os.environ, {}, clear=True):
            assert _try_gemini("test") is None

    @patch("deep_research_team.tools.image_generator.genai.Client")
    def test_api_error(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API error")
        mock_client_cls.return_value = mock_client

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            assert _try_gemini("test") is None


class TestGenerateLogoImage:
    @patch("deep_research_team.tools.image_generator._try_gemini")
    @patch("deep_research_team.tools.image_generator._try_cloudflare")
    def test_cloudflare_primary(self, mock_cf, mock_gemini):
        img_bytes = b"cloudflare_image"
        mock_cf.return_value = img_bytes
        mock_gemini.return_value = b"gemini_image"

        with patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "id", "CLOUDFLARE_API_TOKEN": "tok"}):
            result, error = generate_logo_image("Brand")
        assert result == img_bytes
        assert error is None
        mock_gemini.assert_not_called()

    @patch("deep_research_team.tools.image_generator._try_gemini")
    @patch("deep_research_team.tools.image_generator._try_cloudflare")
    def test_gemini_fallback(self, mock_cf, mock_gemini):
        img_bytes = b"gemini_image"
        mock_cf.return_value = None
        mock_gemini.return_value = img_bytes

        with patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "id", "CLOUDFLARE_API_TOKEN": "tok"}):
            result, error = generate_logo_image("Brand")
        assert result == img_bytes
        assert error is None

    @patch("deep_research_team.tools.image_generator._try_gemini")
    @patch("deep_research_team.tools.image_generator._try_cloudflare")
    def test_all_providers_fail(self, mock_cf, mock_gemini):
        mock_cf.return_value = None
        mock_gemini.return_value = None

        with patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "id", "CLOUDFLARE_API_TOKEN": "tok"}):
            result, error = generate_logo_image("Brand")
        assert result is None
        assert error is not None
        assert "gagal" in error.lower()

    @patch("deep_research_team.tools.image_generator._try_gemini")
    @patch("deep_research_team.tools.image_generator._try_cloudflare")
    def test_skip_cloudflare_if_no_env(self, mock_cf, mock_gemini):
        mock_gemini.return_value = b"gemini_image"

        with patch.dict(os.environ, {}, clear=True):
            result, error = generate_logo_image("Brand")
        assert result == b"gemini_image"
        mock_cf.assert_not_called()

    @patch("deep_research_team.tools.image_generator._try_gemini")
    @patch("deep_research_team.tools.image_generator._try_cloudflare")
    def test_cloudflare_image_too_large_falls_to_gemini(self, mock_cf, mock_gemini):
        mock_cf.return_value = b"x" * (5 * 1024 * 1024 + 1)
        mock_gemini.return_value = b"gemini_ok"

        with patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "id", "CLOUDFLARE_API_TOKEN": "tok"}):
            result, error = generate_logo_image("Brand")
        assert result == b"gemini_ok"
        assert error is None

    @patch("deep_research_team.tools.image_generator._try_gemini")
    @patch("deep_research_team.tools.image_generator._try_cloudflare")
    def test_both_too_large_fails(self, mock_cf, mock_gemini):
        mock_cf.return_value = b"x" * (5 * 1024 * 1024 + 1)
        mock_gemini.return_value = b"y" * (5 * 1024 * 1024 + 1)

        with patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "id", "CLOUDFLARE_API_TOKEN": "tok", "GEMINI_API_KEY": "key"}):
            result, error = generate_logo_image("Brand")
        assert result is None
        assert error is not None

    def test_unknown_style_falls_to_default(self):
        prompt = _build_prompt("Brand", {}, "unknown style here")
        assert "modern minimalis" not in prompt
