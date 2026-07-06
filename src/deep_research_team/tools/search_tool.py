import asyncio
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import time
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import requests
from crewai.tools.base_tool import Tool
from crewai_tools import ScrapeWebsiteTool, SerperDevTool
from pydantic import BaseModel

from deep_research_team.settings import CACHE_DIR, CACHE_TTL, SERPER_TIMEOUT, URL_VALIDATE_TIMEOUT, setup_logging

logger = setup_logging(__name__)

_SEARCH_MARKER_START = "---[SEARCH_RESULT]---"
_SEARCH_MARKER_END = "---[/SEARCH_RESULT]---"
_URL_PATTERN = re.compile(r"https?://[^\s\)\"'\]]+")


def clear_cache() -> None:
    """Remove all cached search results."""
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        logger.info("Cache cleared: %s", CACHE_DIR)


def _cache_key(query: str) -> str:
    return hashlib.md5(query.encode()).hexdigest()


def _read_cache(key: str, ttl: int = CACHE_TTL) -> Any | None:
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        age = time.time() - path.stat().st_mtime
        if age > ttl:
            path.unlink()
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _write_cache(key: str, data: Any) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{key}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _validate_url(url: str, timeout: int = URL_VALIDATE_TIMEOUT) -> bool:
    """Check if a URL is reachable via HEAD request."""
    if not url or not url.startswith("http"):
        return False
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        return resp.status_code < 500
    except requests.RequestException:
        return False


def _validate_organic_results(organic: list[dict]) -> list[dict]:
    """Validate URLs in organic results and add url_valid flag."""
    validated = []
    for item in organic:
        link = item.get("link", "")
        item["url_valid"] = _validate_url(link)
        validated.append(item)
    return validated


def _wrap_json_result(data: dict) -> str:
    """Wrap JSON data in markers so LLM cannot easily fabricate output."""
    encoded = json.dumps(data, ensure_ascii=False, indent=2)
    return f"{_SEARCH_MARKER_START}\n{encoded}\n{_SEARCH_MARKER_END}"


def _get_cached_urls() -> set[str]:
    cached_urls: set[str] = set()
    if not CACHE_DIR.exists():
        return cached_urls
    for fpath in CACHE_DIR.glob("*.json"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("organic", []):
                link = item.get("link", "")
                if link:
                    cached_urls.add(link.rstrip("/"))
        except (json.JSONDecodeError, OSError):
            continue
    return cached_urls


def _is_generic_url(url: str) -> bool:
    """Check if URL is too generic (domain root or home page only)."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if not path:
        return True
    segments = [s for s in path.split("/") if s and not s.startswith("#")]
    return len(segments) <= 1


def _is_url_fake(url: str, cached_urls: set[str]) -> bool:
    """Check if a URL is fake: not in cache AND not reachable via HEAD."""
    if not url:
        return True
    if url.rstrip("/") in cached_urls:
        return False
    return not _validate_url(url)


_MD_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_URL_BARE_PATTERN = re.compile(r"https?://[^\s\)\"'\]]+")


def filter_fake_urls_from_report(report_text: str) -> str:
    """Remove/flag fake and generic URLs from report text.

    - URLs in Serper cache -> kept as-is
    - URLs not in cache but reachable via HEAD -> kept as-is
    - URLs not in cache and unreachable -> REMOVED from text
    - URLs that are domain-root only (no specific path) -> FLAGGED as generic
    """
    cached_urls = _get_cached_urls()
    removed_count = 0
    generic_count = 0

    # Pass 1: remove fake URLs inside markdown links [text](url) -> keep text only
    def _replace_md_link(m: re.Match) -> str:
        nonlocal removed_count
        url = m.group(2)
        if _is_url_fake(url, cached_urls):
            removed_count += 1
            return m.group(1)
        return m.group(0)

    report_text = _MD_LINK_PATTERN.sub(_replace_md_link, report_text)

    # Pass 2: remove fake bare URLs -> replace with placeholder
    def _replace_bare_url(m: re.Match) -> str:
        nonlocal removed_count
        url = m.group(0)
        if _is_url_fake(url, cached_urls):
            removed_count += 1
            return "`[URL dihapus - tidak terverifikasi]`"
        return url

    report_text = _URL_BARE_PATTERN.sub(_replace_bare_url, report_text)

    # Pass 3: flag generic markdown links (reachable but domain-root only)
    def _replace_generic_md(m: re.Match) -> str:
        nonlocal generic_count
        url = m.group(2)
        if _is_generic_url(url):
            generic_count += 1
            return m.group(1)
        return m.group(0)

    report_text = _MD_LINK_PATTERN.sub(_replace_generic_md, report_text)

    # Pass 4: flag generic bare URLs
    def _replace_generic_bare(m: re.Match) -> str:
        nonlocal generic_count
        url = m.group(0)
        if _is_generic_url(url):
            generic_count += 1
            return "`[URL terlalu umum - tidak spesifik]`"
        return url

    report_text = _URL_BARE_PATTERN.sub(_replace_generic_bare, report_text)

    if removed_count > 0 or generic_count > 0:
        parts: list[str] = []
        if removed_count > 0:
            parts.append(
                f"- **{removed_count} URL dihapus** — URL tidak ditemukan di hasil pencarian "
                f"dan tidak dapat diakses saat diperiksa (HTTP HEAD gagal)."
            )
        if generic_count > 0:
            parts.append(
                f"- **{generic_count} URL terlalu umum** — URL hanya mengarah ke halaman utama "
                f"domain, bukan halaman spesifik. LLM tidak boleh mencantumkan homepage "
                f"generik sebagai sumber data."
            )
        summary = (
            "\n\n---\n"
            "**Catatan Sumber:**\n"
            + "\n".join(parts)
            + "\n---\n"
        )
        report_text += summary

    return report_text


def check_serper_api_key() -> tuple[bool, str]:
    key = os.environ.get("SERPER_API_KEY", "")
    if not key:
        return False, "SERPER_API_KEY tidak ditemukan di environment"
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": key, "content-type": "application/json"},
            json={"q": "test", "num": 1},
            timeout=SERPER_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            credits = data.get("credits", 0)
            return True, f"API key valid, credits terpakai: {credits}"
        elif resp.status_code == 401:
            return False, "API key tidak valid (401 Unauthorized)"
        elif resp.status_code == 429:
            return False, "API key kehabisan credits (429 Too Many Requests)"
        else:
            return False, f"Serper API mengembalikan status {resp.status_code}: {resp.text[:200]}"
    except requests.RequestException as e:
        return False, f"Tidak bisa terhubung ke Serper API: {e}"


def _serper_search(search_query: str, retries: int = 2, delay: float = 2.0) -> dict:
    key = _cache_key(search_query)
    cached = _read_cache(key)
    if cached:
        return cached
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            serper = SerperDevTool()
            result = serper._run(search_query=search_query)
            _write_cache(key, result)
            return result
        except requests.RequestException as e:
            last_exc = e
            logger.warning("Serper attempt %d failed (requests error: %s), retrying in %.1fs", attempt, e, delay)
            time.sleep(delay)
        except Exception as e:
            last_exc = e
            logger.error("Serper attempt %d failed (non-requests error: %s)", attempt, e)
            raise
    raise last_exc  # type: ignore[misc]


class SearchInput(BaseModel):
    query: str


class ScrapeInput(BaseModel):
    url: str


class DeepSearchInput(BaseModel):
    field: str


def _search_internet_impl(query: str) -> str:
    try:
        result = _serper_search(query)
    except Exception as e:
        logger.error("Serper search permanently failed for %r: %s", query, e)
        return _wrap_json_result({
            "query": query,
            "error": f"Gagal terhubung ke Serper API setelah beberapa percobaan: {e}",
            "organic": [],
        })
    organic = result.get("organic", [])
    if not organic:
        return _wrap_json_result({"query": query, "organic": [], "message": "Tidak ada hasil ditemukan."})
    organic_validated = _validate_organic_results(organic[:8])
    output = {
        "query": query,
        "organic": organic_validated,
        "total_results": len(organic_validated),
        "source": "serper.dev",
    }
    return _wrap_json_result(output)


def _scrape_website_impl(url: str) -> str:
    try:
        scraper = ScrapeWebsiteTool()
        result = scraper._run(website_url=url)
        text = str(result)
        return text[:4000] if len(text) > 4000 else text
    except Exception as e:
        logger.error("Scrape website failed for %r: %s", url, e)
        return f"Gagal mengambil konten dari {url}: {e}"


_CURRENT_YEAR = str(datetime.now().year)

_QUERY_TEMPLATES = [
    "kompetitor {field} harga fitur",
    "{field} review pelanggan kelemahan",
    "{field} tren pasar {year}",
    "perusahaan {field} terbaik Indonesia",
    "strategi pemasaran {field}",
]


def _run_async(coro: Any) -> Any:
    """Run coroutine safely — works with or without a running event loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def _deep_search_impl(field: str) -> str:
    queries = [t.format(field=field, year=_CURRENT_YEAR) for t in _QUERY_TEMPLATES]

    async def _run_all() -> list[dict]:
        tasks = [asyncio.to_thread(_serper_search, q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid: list[dict] = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logger.warning("Deep search query %r failed: %s", queries[i], r)
            else:
                valid.append(r)
        return valid

    all_results = _run_async(_run_all())

    seen_links: set[str] = set()
    combined: list[dict] = []
    for raw in all_results:
        organic = raw.get("organic", [])
        for item in organic:
            link = item.get("link", "")
            if link and link not in seen_links:
                seen_links.add(link)
                combined.append({
                    "title": item.get("title", ""),
                    "link": link,
                    "snippet": item.get("snippet", ""),
                    "url_valid": _validate_url(link),
                })

    output = {
        "field": field,
        "queries": queries,
        "organic": combined[:20],
        "total_queries": len(queries),
        "total_results": len(combined[:20]),
        "source": "serper.dev",
    }
    return _wrap_json_result(output)


search_internet = Tool(
    name="Cari di Internet",
    description="Cari informasi di internet menggunakan Serper. Gunakan untuk mencari data kompetitor, harga, fitur, review, atau informasi umum tentang suatu topik. Input: query pencarian teks.",
    args_schema=SearchInput,
    func=_search_internet_impl,
)

scrape_website = Tool(
    name="Scrape Halaman Website",
    description="Ambil konten teks dari sebuah halaman website. Gunakan untuk mengambil data detail dari URL yang ditemukan dari hasil pencarian. Input: URL lengkap (https://...).",
    args_schema=ScrapeInput,
    func=_scrape_website_impl,
)

deep_search = Tool(
    name="Deep Search Kompetitor",
    description="Lakukan pencarian mendalam dengan banyak query paralel. Cocok untuk riset awal kompetitor. Input: bidang bisnis (contoh: E-commerce Fesyen).",
    args_schema=DeepSearchInput,
    func=_deep_search_impl,
)
