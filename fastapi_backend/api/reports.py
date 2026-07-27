from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse, PlainTextResponse

from deep_research_team.backend import get_brand_concepts, get_brand_names
from deep_research_team.settings import setup_logging
from deep_research_team.tools.db_utils import get_history_row
from deep_research_team.tools.export_utils import md_to_html, md_to_pdf
from deep_research_team.tools.storage import read_text as read_stored_text

from fastapi_backend.core.deps import get_report_path

logger = setup_logging(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{row_id}")
async def get_report(row_id: int) -> dict[str, Any]:
    row = get_history_row(row_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if row["status"] != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Report status is {row['status']}")

    report_path = get_report_path(row_id)
    content = read_stored_text(str(report_path))

    return {
        "id": row["id"],
        "field": row["field"],
        "status": row["status"],
        "created_at": row["created_at"],
        "content": content,
    }


@router.get("/{row_id}/export/{fmt}")
async def export_report(row_id: int, fmt: str) -> Any:
    report_path = get_report_path(row_id)
    content = read_stored_text(str(report_path))

    if fmt == "md":
        return PlainTextResponse(content, media_type="text/markdown",
                headers={"Content-Disposition": f"attachment; filename=laporan_{row_id}.md"})
    elif fmt == "html":
        html = md_to_html(content)
        return HTMLResponse(html)
    elif fmt == "pdf":
        pdf_bytes = md_to_pdf(content)
        if pdf_bytes is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="PDF generation failed")
        from fastapi.responses import Response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=laporan_{row_id}.pdf"},
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Unsupported format: {fmt}. Use md, html, or pdf.")


@router.post("/{row_id}/branding/concepts")
async def get_brand_concepts_endpoint(row_id: int) -> dict[str, Any]:
    report_path = get_report_path(row_id)
    content = read_stored_text(str(report_path))
    concepts = get_brand_concepts(content)
    names = get_brand_names(content)
    return {"concepts": [c.to_dict() for c in concepts], "names": names}
