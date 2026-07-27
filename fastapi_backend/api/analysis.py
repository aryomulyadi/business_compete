import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from deep_research_team.settings import setup_logging

from deep_research_team.tools.db_utils import save_history
from fastapi_backend.workers.progress_store import create_task, get_task

logger = setup_logging(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/start")
async def start_analysis(payload: dict[str, str]) -> dict[str, Any]:
    business_field = (payload.get("business_field") or "").strip()
    if not business_field:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="business_field is required")
    if len(business_field) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="business_field too short (min 10 characters)",
        )

    task_id = str(uuid.uuid4())
    row_id = save_history(business_field, "pending")
    create_task(task_id, business_field, row_id)

    return {"task_id": task_id, "field": business_field, "row_id": row_id}


@router.get("/status/{task_id}")
async def get_status(task_id: str) -> dict[str, Any]:
    tp = get_task(task_id)
    if tp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return tp.to_dict()
