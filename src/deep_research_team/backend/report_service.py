import re
from pathlib import Path
from typing import Optional

from deep_research_team.backend.models import BrandConcept
from deep_research_team.tools.export_utils import find_brand_section


def read_report(report_path: Path) -> Optional[str]:
    if not report_path.exists():
        return None
    with open(report_path, "r", encoding="utf-8") as f:
        return f.read()


def get_brand_names(report: str) -> list[str]:
    names: list[str] = []
    section = find_brand_section(report)
    if section:
        for line in section.split("\n"):
            line = line.strip()
            if line.startswith("- **") or line.startswith("* **"):
                name = re.sub(r'^[-*]\s*\*\*(.*?)\*\*.*', r'\1', line)
                if name and name != line:
                    names.append(name)
    return names


_BLOCK_RE = re.compile(
    r'(?m)^[-*]\s+\*\*(.+?)\*\*[:\s]*(.*?)(?=^[-*]\s+\*\*|\Z)',
    re.DOTALL,
)
_BLOCK_FALLBACK = re.compile(
    r'(?m)^\d+[.)]\s*\*\*(.+?)\*\*[:\s]*(.*?)(?=^\d+[.)]\s*\*\*|\Z)',
    re.DOTALL,
)


def _extract_field(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.DOTALL)
    if m:
        return m.group(1).strip().rstrip(".,")
    return ""


def get_brand_concepts(report: str) -> list[BrandConcept]:
    section = find_brand_section(report)
    if not section:
        return []

    matches: list[re.Match] = []
    for block_re in (_BLOCK_RE, _BLOCK_FALLBACK):
        matches = list(block_re.finditer(section))
        if matches:
            break

    brands: list[BrandConcept] = []
    for block in matches:
        name = block.group(1).strip()
        body = block.group(2)
        meaning = _extract_field(
            body,
            r'(?:Makna|makna)[:\s]+(.+?)(?=\n(?:Filosofi|filosofi|Target|target|Positioning|positioning)|$)',
        )
        philosophy = _extract_field(
            body,
            r'(?:Filosofi|filosofi)[:\s]+(.+?)(?=\n(?:Makna|makna|Target|target|Positioning|positioning)|$)',
        )
        target = _extract_field(
            body,
            r'(?:Target Pasar|target pasar|Target|target)[:\s]+(.+?)(?=\n(?:Makna|makna|Filosofi|filosofi|Positioning|positioning)|$)',
        )
        positioning = _extract_field(
            body,
            r'(?:Positioning|positioning)[:\s]+(.+?)(?=\n(?:Makna|makna|Filosofi|filosofi|Target|target)|$)',
        )
        brands.append(BrandConcept(name, meaning, philosophy, target, positioning))
    return brands
