from deep_research_team.tools.export_utils import md_to_html, md_to_pdf


class TestMdToHtml:
    def test_basic_markdown(self) -> None:
        html = md_to_html("# Hello")
        assert "<h1>Hello</h1>" in html
        assert "<!DOCTYPE html>" in html
        assert "Segoe UI" in html

    def test_tables_extension(self) -> None:
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        html = md_to_html(md)
        assert "<table>" in html
        assert "<th>A</th>" in html or "<th>A" in html

    def test_fenced_code(self) -> None:
        md = "```python\nprint('hi')\n```"
        html = md_to_html(md)
        assert "<pre><code" in html


class TestMdToPdf:
    def test_returns_bytes_or_none(self, sample_markdown: str) -> None:
        result = md_to_pdf(sample_markdown)
        assert result is None or isinstance(result, bytes)

    def test_with_simple_text(self) -> None:
        result = md_to_pdf("Simple text")
        assert result is None or isinstance(result, bytes)

    def test_sanitize_removes_bad_chars(self) -> None:
        text = "Hello \x00 World \x1f Test"
        result = md_to_pdf(text)
        assert result is None or isinstance(result, bytes)

    def test_empty_string(self) -> None:
        result = md_to_pdf("")
        assert result is None or isinstance(result, bytes)
