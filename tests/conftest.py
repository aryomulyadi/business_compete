from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Generator[Path, None, None]:
    original = None
    try:
        from deep_research_team import settings as s
        original = s.OUTPUT_DIR, s.CACHE_DIR, s.DB_PATH, s.REPORT_FILE
        s.OUTPUT_DIR = tmp_path
        s.CACHE_DIR = tmp_path / "cache"
        s.DB_PATH = tmp_path / "history.db"
        s.REPORT_FILE = tmp_path / "laporan_analisis_kompetitor.md"
        yield tmp_path
    finally:
        if original:
            s.OUTPUT_DIR, s.CACHE_DIR, s.DB_PATH, s.REPORT_FILE = original


@pytest.fixture
def sample_markdown() -> str:
    return (
        "# Laporan Analisis\n\n"
        "## SWOT\n\n"
        "- **Kekuatan**: Branding kuat\n"
        "- **Kelemahan**: Harga mahal\n\n"
        "| Perusahaan | Harga |\n"
        "|-----------|------|\n"
        "| PT A | Rp10.000 |\n"
        "| PT B | Rp8.000 |\n\n"
        "Sumber: [contoh](https://example.com)\n"
    )
