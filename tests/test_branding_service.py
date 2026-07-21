from unittest.mock import patch

from deep_research_team.backend.branding_service import (
    generate_ai_logo,
    generate_svg_logo,
    save_logo_entry,
)


class TestGenerateAiLogo:
    @patch("deep_research_team.backend.branding_service.generate_logo_image")
    def test_delegates_to_image_generator(self, mock_gen):
        mock_gen.return_value = (b"img_data", None)
        result, error = generate_ai_logo("Test Brand", {}, "modern minimalis")
        assert result == b"img_data"
        assert error is None
        mock_gen.assert_called_once_with("Test Brand", {}, "modern minimalis")

    @patch("deep_research_team.backend.branding_service.generate_logo_image")
    def test_passes_error(self, mock_gen):
        mock_gen.return_value = (None, "Error message")
        result, error = generate_ai_logo("Test Brand")
        assert result is None
        assert error == "Error message"

    @patch("deep_research_team.backend.branding_service.generate_logo_image")
    def test_default_concept_is_none(self, mock_gen):
        mock_gen.return_value = (b"img", None)
        generate_ai_logo("Brand")
        mock_gen.assert_called_once_with("Brand", None, "modern minimalis")


class TestGenerateSvgLogo:
    @patch("deep_research_team.backend.branding_service.generate_logo_svg")
    def test_delegates_to_export_utils(self, mock_svg):
        mock_svg.return_value = "<svg>mock</svg>"
        result = generate_svg_logo("Test Brand")
        assert result == "<svg>mock</svg>"
        mock_svg.assert_called_once_with("Test Brand")


class TestSaveLogoEntry:
    @patch("deep_research_team.backend.branding_service.save_logo")
    def test_saves_with_json_concept(self, mock_save):
        mock_save.return_value = 42
        result = save_logo_entry(
            history_row_id=1,
            brand_name="Brand",
            concept={"key": "value"},
            svg="<svg/>",
            style="modern minimalis",
        )
        assert result == 42
        call_kwargs = mock_save.call_args[1]
        assert '"key": "value"' in call_kwargs["concept"]
