import re
from pathlib import Path
from typing import Optional

import requests

from deep_research_team.backend.models import BrandConcept
from deep_research_team.settings import setup_logging
from deep_research_team.tools.export_utils import find_brand_section
from deep_research_team.tools.storage import read_text as read_stored_text

logger = setup_logging(__name__)

# Pattern untuk menangkap nama brand dari berbagai format LLM
_BRAND_NAME_PATTERNS = [
    re.compile(r'^#{3,4}\s+Opsi\s+\d+:\s*\*\*([^*]+?)\*\*'),
    re.compile(r'^#{3,4}\s+Opsi\s+\d+:\s*"([^"]+)"'),
    re.compile(r'^#{3,4}\s+Opsi\s+\d+:\s+(.+)$'),
    re.compile(r'^\*\*Opsi\s+\d+:\s+(.+?)\*\*'),
    re.compile(r'^\*\*\d+[.)]\s+([^*]+?)\*\*'),
    re.compile(r'^-\s+\*\*([^*]+?)\*\*'),
    re.compile(r'^\*\s+\*\*([^*]+?)\*\*'),
    re.compile(r'^\d+[.)]\s+\*\*([^*]+?)\*\*'),
    re.compile(r'^[-\d.)•\s]+\*\*([^*]+?)\*\*'),
    re.compile(r'^[-*\d.)•\s]+([A-Z][A-Za-z\s&/-]{1,60}?):\s'),
]

_SKIP_WORDS = {
    "opsi", "nama brand", "contoh", "strategi", "rekomendasi", "brand",
    "makna", "filosofi", "positioning", "differentiation", "diferensiasi",
    "target", "audience", "pasar", "literal",
}


def read_report(report_path: str | Path) -> Optional[str]:
    try:
        return read_stored_text(str(report_path))
    except (OSError, ValueError, requests.RequestException):
        return None


def get_brand_names(report: str) -> list[str]:
    names: list[str] = []
    section = find_brand_section(report)
    if not section:
        logger.info("No Brand Strategy section found in report")
        return names

    for line in section.split("\n"):
        line = line.strip()
        if not line:
            continue

        name = ""
        for pat in _BRAND_NAME_PATTERNS:
            m = pat.search(line)
            if m:
                name = m.group(1).strip().rstrip(":;.,")
                break

        if not name or len(name) < 2:
            continue

        lower = name.lower()
        if any(re.search(rf'\b{re.escape(kw)}\b', lower) for kw in _SKIP_WORDS):
            continue

        names.append(name)

    logger.info("Found %d brand names in section", len(names))
    return names


_BLOCK_PATTERNS = [
    re.compile(
        r'(?m)^####\s+Opsi\s+\d+:\s*\*\*(.+?)\*\*[\s:]*(.*?)(?=^####\s+Opsi|\Z)', re.DOTALL
    ),
    re.compile(
        r'(?m)^####\s+Opsi\s+\d+:\s*"([^"]+)"[\s:]*(.*?)(?=^####\s+Opsi|\Z)', re.DOTALL
    ),
    re.compile(
        r'(?m)^###\s+Opsi\s+\d+:\s*\*\*(.+?)\*\*[\s:]*(.*?)(?=^###\s+Opsi|\Z)', re.DOTALL
    ),
    re.compile(
        r'(?m)^###\s+Opsi\s+\d+:\s+(.+?)$(.*?)(?=^###\s+Opsi|\Z)', re.DOTALL
    ),
    re.compile(
        r'(?m)^\*\*Opsi\s+\d+:\s+(.+?)\*\*([\s\S]*?)(?=^\*\*Opsi\s+\d+:|\Z)', re.DOTALL
    ),
    re.compile(
        r'(?m)^\*\*\d+[.)]\s+([^*]+?)\*\*([\s\S]*?)(?=^\*\*\d+[.)]|\Z)', re.DOTALL
    ),
    re.compile(
        r'(?m)^[-*]\s+\*\*(.+?)\*\*[:\s]*(.*?)(?=^[-*]\s+\*\*|\Z)', re.DOTALL
    ),
    re.compile(
        r'(?m)^\d+[.)]\s*\*\*(.+?)\*\*[:\s]*(.*?)(?=^\d+[.)]\s*\*\*|\Z)', re.DOTALL
    ),
    re.compile(
        r'(?m)^[-*]\s+([A-Z][A-Za-z\s&/-]{2,60}?):\s*(.*?)(?=^[-*]\s+[A-Z]|^\d+[.)]|\Z)',
        re.DOTALL,
    ),
    re.compile(
        r'(?m)^\d+[.)]\s+([A-Z][A-Za-z\s&/-]{2,60}?):\s*(.*?)(?=^\d+[.)]|\Z)',
        re.DOTALL,
    ),
]

_FIELD_PATTERNS: dict[str, re.Pattern] = {
    "meaning": re.compile(
        r"(?:Makna|makna)\s*(?:kata|literal|nama)?[:\s]+(.+?)"
        r"(?=\n[\s\-*#]*(?:Filosofi|filosofi|Target|target|Positioning|positioning)|\Z)",
        re.DOTALL | re.IGNORECASE,
    ),
    "philosophy": re.compile(
        r"(?:Filosofi|filosofi|filosofi\s+brand)[:\s]+(.+?)"
        r"(?=\n[\s\-*#]*(?:Makna|makna|Target|target|Positioning|positioning)|\Z)",
        re.DOTALL | re.IGNORECASE,
    ),
    "target_market": re.compile(
        r"(?:Target\s+Pasar|target\s+pasar|Target|target|"
        r"target\s+audience|target\s+market|target\s+audiens)[:\s]+(.+?)"
        r"(?=\n[\s\-*#]*(?:Makna|makna|Filosofi|filosofi|Positioning|positioning)|\Z)",
        re.DOTALL | re.IGNORECASE,
    ),
    "positioning": re.compile(
        r"(?:Positioning|positioning|Posisi|posisi|Posisi\s+Brand|"
        r"strategi\s+positioning)[:\s]+(.+?)"
        r"(?=\n[\s\-*#]*(?:Makna|makna|Filosofi|filosofi|Target|target)|\Z)",
        re.DOTALL | re.IGNORECASE,
    ),
}


def _extract_field(body: str, field_pattern: re.Pattern) -> str:
    m = field_pattern.search(body)
    if m:
        value = m.group(1).strip().rstrip(".,;")
        value = re.sub(r'^[*#>\-\s]+', '', value).strip()
        return value
    return ""


def get_brand_concepts(report: str) -> list[BrandConcept]:
    section = find_brand_section(report)
    if not section:
        logger.info("No Brand Strategy section for concept extraction")
        return []

    matches: list[re.Match] = []
    for block_re in _BLOCK_PATTERNS:
        matches = list(block_re.finditer(section))
        if matches:
            logger.info("Using block pattern: %s", block_re.pattern[:60])
            break

    if not matches:
        logger.warning("No brand blocks found in section")
        return []

    brands: list[BrandConcept] = []
    for block in matches:
        name = (block.group(1) or "").strip()
        body = block.group(2) if block.lastindex and block.lastindex >= 2 else ""
        meaning = _extract_field(body, _FIELD_PATTERNS["meaning"])
        philosophy = _extract_field(body, _FIELD_PATTERNS["philosophy"])
        target = _extract_field(body, _FIELD_PATTERNS["target_market"])
        positioning = _extract_field(body, _FIELD_PATTERNS["positioning"])
        brands.append(BrandConcept(name, meaning, philosophy, target, positioning))

    logger.info("Extracted %d brand concepts", len(brands))
    return brands
