import asyncio
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from crewai.tools import tool
from crewai_tools import ScrapeWebsiteTool, SerperDevTool

CACHE_DIR = "output/cache"
_SEARCH_MARKER_START = "---[SEARCH_RESULT]---"
_SEARCH_MARKER_END = "---[/SEARCH_RESULT]---"
_URL_PATTERN = re.compile(r"https?://[^\s\)\"'\]]+")


def _cache_key(query: str) -> str:
    return hashlib.md5(query.encode()).hexdigest()


def _read_cache(key: str) -> Any | None:
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _write_cache(key: str, data: Any) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{key}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _validate_url(url: str, timeout: int = 5) -> bool:
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
    """Collect all URLs that exist in Serper cache (proven real)."""
    cached_urls: set[str] = set()
    cache_dir = Path(CACHE_DIR)
    if not cache_dir.exists():
        return cached_urls
    for fpath in cache_dir.glob("*.json"):
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
    """Remove fake URLs from report text.
    - URLs in Serper cache -> kept as-is
    - URLs not in cache but reachable via HEAD -> kept as-is
    - URLs not in cache and unreachable -> REMOVED from text
    """
    cached_urls = _get_cached_urls()
    removed_count = 0

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

    if removed_count > 0:
        summary = (
            f"\n\n---\n"
            f"**Catatan:** {removed_count} URL dihapus karena tidak lolos verifikasi: "
            f"URL tidak ditemukan di hasil pencarian Serper **dan** tidak dapat diakses "
            f"saat diperiksa (HTTP HEAD gagal). "
            f"Hanya URL yang terverifikasi (berasal dari hasil pencarian atau dapat dijangkau) yang dipertahankan.\n"
            f"---\n"
        )
        report_text += summary

    return report_text


def check_serper_api_key() -> tuple[bool, str]:
    """Verify Serper API key is valid and has credits remaining."""
    key = os.environ.get("SERPER_API_KEY", "")
    if not key:
        return False, "SERPER_API_KEY tidak ditemukan di environment"
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": key, "content-type": "application/json"},
            json={"q": "test", "num": 1},
            timeout=10,
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


def _serper_search(search_query: str) -> dict:
    key = _cache_key(search_query)
    cached = _read_cache(key)
    if cached:
        return cached
    serper = SerperDevTool()
    result = serper._run(search_query=search_query)
    _write_cache(key, result)
    return result


@tool("Cari di Internet")
def search_internet(query: str) -> str:
    """Cari informasi di internet menggunakan Serper. Gunakan untuk mencari data kompetitor, harga, fitur, review, atau informasi umum tentang suatu topik. Input: query pencarian teks."""
    result = _serper_search(query)
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


@tool("Scrape Halaman Website")
def scrape_website(url: str) -> str:
    """Ambil konten teks dari sebuah halaman website. Gunakan untuk mengambil data detail dari URL yang ditemukan dari hasil pencarian. Input: URL lengkap (https://...)."""
    scraper = ScrapeWebsiteTool()
    result = scraper._run(website_url=url)
    text = str(result)
    return text[:4000] if len(text) > 4000 else text


_CURRENT_YEAR = str(datetime.now().year)

_QUERY_TEMPLATES = [
    "kompetitor {field} harga fitur",
    "{field} review pelanggan kelemahan",
    "{field} tren pasar {year}",
    "perusahaan {field} terbaik Indonesia",
    "strategi pemasaran {field}",
]


@tool("Deep Search Kompetitor")
def deep_search(field: str) -> str:
    """Lakukan pencarian mendalam dengan banyak query paralel. Cocok untuk riset awal kompetitor. Input: bidang bisnis (contoh: E-commerce Fesyen)."""
    queries = [t.format(field=field, year=_CURRENT_YEAR) for t in _QUERY_TEMPLATES]

    async def _run_all() -> list[dict]:
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(None, _serper_search, q) for q in queries]
        return await asyncio.gather(*tasks)

    all_results = asyncio.run(_run_all())

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
