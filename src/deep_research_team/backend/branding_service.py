import json
from typing import Optional

from deep_research_team.backend.models import LogoItem
from deep_research_team.tools.db_utils import get_logos, save_logo
from deep_research_team.tools.export_utils import generate_logo_svg
from deep_research_team.tools.gemini_image import generate_logo_image


def generate_svg_logo(brand_name: str) -> str:
    return generate_logo_svg(brand_name)


def generate_ai_logo(
    brand_name: str,
    concept: Optional[dict] = None,
    style: str = "modern minimalis",
) -> tuple[Optional[bytes], Optional[str]]:
    return generate_logo_image(brand_name, concept, style)


def save_logo_entry(
    history_row_id: int,
    brand_name: str,
    concept: dict,
    svg: str = "",
    png_path: str = "",
    style: str = "",
) -> int:
    return save_logo(
        history_row_id=history_row_id,
        brand_name=brand_name,
        concept=json.dumps(concept),
        svg=svg,
        png_path=png_path,
        style=style,
    )


def get_logo_history(history_row_id: int) -> list[LogoItem]:
    rows = get_logos(history_row_id)
    return [LogoItem.from_row((
        r["id"], r["history_row_id"], r["brand_name"],
        r["concept"], r["svg"], r["png_path"],
        r["style"], r["created_at"],
    )) for r in rows]
