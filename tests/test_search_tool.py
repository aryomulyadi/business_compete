import json
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("crewai")
pytest.importorskip("crewai_tools")

from deep_research_team.tools.search_tool import (
    _cache_key,
    _get_cached_urls,
    _is_url_fake,
    _scrape_website_impl,
    _search_internet_impl,
    _serper_search,
    _validate_url,
    _wrap_json_result,
    filter_fake_urls_from_report,
)


class TestCacheKey:
    def test_returns_md5_hexdigest(self) -> None:
        key = _cache_key("test query")
        assert isinstance(key, str)
        assert len(key) == 32

    def test_deterministic(self) -> None:
        assert _cache_key("hello") == _cache_key("hello")

    def test_different_inputs(self) -> None:
        assert _cache_key("a") != _cache_key("b")


class TestWrapJsonResult:
    def test_wraps_in_markers(self) -> None:
        data = {"key": "value"}
        result = _wrap_json_result(data)
        assert "---[SEARCH_RESULT]---" in result
        assert "---[/SEARCH_RESULT]---" in result

    def test_valid_json_inside(self) -> None:
        data = {"num": 42}
        result = _wrap_json_result(data)
        inner = result.split("---[SEARCH_RESULT]---")[1].split("---[/SEARCH_RESULT]---")[0].strip()
        assert json.loads(inner) == data


class TestValidateUrl:
    def test_empty_string(self) -> None:
        assert not _validate_url("", timeout=1)

    def test_non_http(self) -> None:
        assert not _validate_url("ftp://bad.com", timeout=1)

    def test_invalid_url_returns_false(self) -> None:
        assert not _validate_url("not a url", timeout=1)

    @patch("deep_research_team.tools.search_tool.requests.head")
    def test_reachable_url(self, mock_head) -> None:
        mock_head.return_value.status_code = 200
        assert _validate_url("https://example.com", timeout=1)

    @patch("deep_research_team.tools.search_tool.requests.head")
    def test_unreachable_url(self, mock_head) -> None:
        from requests import RequestException
        mock_head.side_effect = RequestException("timeout")
        assert not _validate_url("https://example.com", timeout=1)


class TestGetCachedUrls:
    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        from deep_research_team import settings as s
        import deep_research_team.tools.search_tool as st
        orig_s = s.CACHE_DIR
        orig_st = st.CACHE_DIR
        s.CACHE_DIR = tmp_path / "nonexistent"
        st.CACHE_DIR = tmp_path / "nonexistent"
        try:
            assert _get_cached_urls() == set()
        finally:
            s.CACHE_DIR = orig_s
            st.CACHE_DIR = orig_st

    def test_with_cache_file(self, tmp_path: Path) -> None:
        from deep_research_team import settings as s
        import deep_research_team.tools.search_tool as st
        orig_s = s.CACHE_DIR
        orig_st = st.CACHE_DIR
        s.CACHE_DIR = tmp_path
        st.CACHE_DIR = tmp_path
        try:
            data = {"organic": [{"link": "https://example.com"}, {"link": "https://test.org"}]}
            cache_file = tmp_path / "abc123.json"
            cache_file.write_text(json.dumps(data), encoding="utf-8")
            urls = _get_cached_urls()
            assert "https://example.com" in urls
            assert "https://test.org" in urls
        finally:
            s.CACHE_DIR = orig_s
            st.CACHE_DIR = orig_st

    def test_skip_invalid_json(self, tmp_path: Path) -> None:
        from deep_research_team import settings as s
        import deep_research_team.tools.search_tool as st
        orig_s = s.CACHE_DIR
        orig_st = st.CACHE_DIR
        s.CACHE_DIR = tmp_path
        st.CACHE_DIR = tmp_path
        try:
            (tmp_path / "bad.json").write_text("not json", encoding="utf-8")
            assert _get_cached_urls() == set()
        finally:
            s.CACHE_DIR = orig_s
            st.CACHE_DIR = orig_st


class TestIsUrlFake:
    def test_empty_url(self) -> None:
        assert _is_url_fake("", set())

    def test_url_in_cache(self) -> None:
        assert not _is_url_fake("https://example.com", {"https://example.com"})

    def test_url_with_trailing_slash(self) -> None:
        assert not _is_url_fake("https://example.com/", {"https://example.com"})

    @patch("deep_research_team.tools.search_tool._validate_url")
    def test_url_not_in_cache_but_reachable(self, mock_validate) -> None:
        mock_validate.return_value = True
        assert not _is_url_fake("https://example.com", set())

    @patch("deep_research_team.tools.search_tool._validate_url")
    def test_url_not_in_cache_and_unreachable(self, mock_validate) -> None:
        mock_validate.return_value = False
        assert _is_url_fake("https://example.com", set())


class TestFilterFakeUrlsFromReport:
    def test_no_urls(self) -> None:
        text = "Laporan tanpa URL"
        result = filter_fake_urls_from_report(text)
        assert result == text

    @patch("deep_research_team.tools.search_tool._is_url_fake", return_value=True)
    def test_removes_fake_markdown_links(self, mock_is_fake) -> None:
        text = "Lihat [situs ini](https://fake.com)"
        result = filter_fake_urls_from_report(text)
        assert "situs ini" in result
        assert "https://fake.com" not in result

    def test_keeps_real_markdown_links(self) -> None:
        text = "Lihat [situs ini](https://real.com/artikel/harga)"
        with patch(
            "deep_research_team.tools.search_tool._is_url_fake",
            return_value=False,
        ):
            result = filter_fake_urls_from_report(text)
            assert "https://real.com/artikel/harga" in result

    def test_adds_summary_when_urls_removed(self) -> None:
        text = "Link: [fake](https://fake1.com) dan [fake2](https://fake2.com)"
        result = filter_fake_urls_from_report(text)
        assert "Catatan Sumber" in result
        assert "URL dihapus" in result

    def test_flags_generic_urls(self) -> None:
        text = "Sumber: [Shopee](https://shopee.co.id)"
        with patch(
            "deep_research_team.tools.search_tool._is_url_fake",
            return_value=False,
        ):
            result = filter_fake_urls_from_report(text)
            assert "URL terlalu umum" in result
            assert "Catatan Sumber" in result


class TestSerperSearch:
    @patch("deep_research_team.tools.search_tool.SerperDevTool")
    def test_retry_on_requests_error_then_success(self, mock_serper_cls) -> None:
        from requests.exceptions import ConnectionError as ConnErr
        mock_instance = mock_serper_cls.return_value
        mock_instance._run.side_effect = [
            ConnErr("connection refused"),
            {"organic": [{"link": "https://example.com", "title": "Test", "snippet": "desc"}]},
        ]
        with patch("deep_research_team.tools.search_tool._read_cache", return_value=None):
            with patch("deep_research_team.tools.search_tool._write_cache"):
                result = _serper_search("test query")
        assert "organic" in result
        assert mock_instance._run.call_count == 2

    @patch("deep_research_team.tools.search_tool.SerperDevTool")
    def test_all_retries_exhausted_raises(self, mock_serper_cls) -> None:
        from requests.exceptions import ConnectionError as ConnErr
        mock_instance = mock_serper_cls.return_value
        mock_instance._run.side_effect = ConnErr("always fails")
        with patch("deep_research_team.tools.search_tool._read_cache", return_value=None):
            with pytest.raises(Exception, match="always fails"):
                _serper_search("test query")


class TestSearchInternetImpl:
    def test_returns_wrapped_json_on_success(self) -> None:
        fake_result = {"organic": [{"link": "https://a.com", "title": "A", "snippet": "a"}]}
        with patch("deep_research_team.tools.search_tool._serper_search", return_value=fake_result):
            result = _search_internet_impl("test")
        assert "---[SEARCH_RESULT]---" in result

    def test_returns_error_json_on_serper_failure(self) -> None:
        with patch(
            "deep_research_team.tools.search_tool._serper_search",
            side_effect=Exception("Serper API timeout"),
        ):
            result = _search_internet_impl("test")
        assert "Gagal terhubung" in result
        assert "---[SEARCH_RESULT]---" in result


class TestScrapeWebsiteImpl:
    @patch("deep_research_team.tools.search_tool.ScrapeWebsiteTool")
    def test_returns_truncated_text(self, mock_scraper_cls) -> None:
        mock_instance = mock_scraper_cls.return_value
        mock_instance._run.return_value = "x" * 5000
        result = _scrape_website_impl("https://example.com")
        assert len(result) == 4000

    @patch("deep_research_team.tools.search_tool.ScrapeWebsiteTool")
    def test_returns_error_on_exception(self, mock_scraper_cls) -> None:
        mock_instance = mock_scraper_cls.return_value
        mock_instance._run.side_effect = Exception("timeout")
        result = _scrape_website_impl("https://example.com")
        assert "Gagal mengambil konten" in result
        assert "timeout" in result
