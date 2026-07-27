import asyncio
import base64
import json
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse, RedirectResponse

from deep_research_team.backend import (
    generate_ai_logo,
    get_brand_names,
    get_history_list,
    get_logo_history,
    read_report,
    save_logo_entry,
)
from deep_research_team.settings import setup_logging
from deep_research_team.tools.image_generator import STYLE_PROMPTS
from deep_research_team.tools.export_utils import generate_logo_svg
from deep_research_team.tools.storage import upload_bytes

logger = setup_logging(__name__)
router = APIRouter(prefix="/api/branding", tags=["branding"])
LOGOS_DIR = Path("output/logos")


@router.get("/concepts")
async def list_brand_concepts(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """List completed reports that have brand concepts."""
    all_items = get_history_list(limit=9999, offset=0)

    branded: list[dict[str, Any]] = []
    for item in all_items:
        if item.status != "completed":
            continue
        if not item.report_path:
            continue
        content = read_report(item.report_path)
        if not content:
            continue
        names = get_brand_names(content)
        if not names:
            continue
        branded.append({
            "row_id": item.id,
            "field": item.field,
            "created_at": item.created_at,
            "brand_names": names,
        })

    branded.sort(key=lambda r: r["row_id"], reverse=True)
    total = len(branded)
    sliced = branded[offset:offset + limit]

    return {
        "reports": sliced,
        "offset": offset,
        "limit": limit,
        "total": total,
    }


@router.get("/styles")
async def get_styles() -> dict[str, Any]:
    return {"styles": list(STYLE_PROMPTS.keys())}


@router.post("/logo/svg")
async def create_svg_logo(payload: dict[str, Any]) -> dict[str, Any]:
    brand_name = (payload.get("brand_name") or "").strip()
    if not brand_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="brand_name is required")
    size = int(payload.get("size", 200))
    svg = generate_logo_svg(brand_name, size)
    return {"svg": svg, "brand_name": brand_name}


@router.post("/logo/ai")
async def create_ai_logo(payload: dict[str, Any]) -> dict[str, Any]:
    brand_name = (payload.get("brand_name") or "").strip()
    concept_raw = payload.get("concept")
    style = (payload.get("style") or "modern minimalis").strip()
    history_row_id = payload.get("history_row_id")

    if not brand_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="brand_name is required")

    concept_dict: Optional[dict] = None
    if concept_raw:
        if isinstance(concept_raw, dict):
            concept_dict = concept_raw
        elif isinstance(concept_raw, str):
            try:
                concept_dict = json.loads(concept_raw)
            except json.JSONDecodeError:
                concept_dict = {"description": concept_raw}

    image_bytes, error = await asyncio.to_thread(generate_ai_logo, brand_name, concept_dict, style)

    if image_bytes:
        safe_name = brand_name.replace(" ", "_").replace("/", "_")
        safe_style = style.replace(" ", "_").replace("/", "_")
        logo_filename = f"{safe_name}_{safe_style}_{int(time.time())}.png"
        png_location = upload_bytes(f"logos/{logo_filename}", image_bytes, "image/png")

        b64 = base64.b64encode(image_bytes).decode("utf-8")

        if history_row_id:
            save_logo_entry(
                history_row_id=int(history_row_id),
                brand_name=brand_name,
                concept=concept_dict or {},
                svg="",
                png_path=png_location,
                style=style,
            )

        return {"image_base64": b64, "svg": None, "error": None}

    svg = generate_logo_svg(brand_name)
    if history_row_id:
        save_logo_entry(
            history_row_id=int(history_row_id),
            brand_name=brand_name,
            concept=concept_dict or {},
            svg=svg,
            png_path="",
            style=style,
        )
    return {"image_base64": None, "svg": svg, "error": None}


@router.get("/logo/file/{filename}")
async def get_logo_file(filename: str):
    if filename.startswith(("https%3A", "http%3A")):
        from urllib.parse import unquote
        return RedirectResponse(unquote(filename))
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    filepath = LOGOS_DIR / filename
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, media_type="image/png")


@router.get("/logo/history/{history_row_id}")
async def get_logo_history_endpoint(history_row_id: int) -> dict[str, Any]:
    logos = get_logo_history(history_row_id)
    return {"logos": [logo.to_dict() if hasattr(logo, "to_dict") else logo for logo in logos]}
