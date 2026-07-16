from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status

from deep_research_team.backend import get_history_count, get_history_item, get_history_list
from deep_research_team.settings import setup_logging

logger = setup_logging(__name__)

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
async def list_history(
    search: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    items = get_history_list(limit=limit, offset=offset, search=search)
    total = get_history_count(search=search)
    return {
        "items": [h.to_dict() for h in items],
        "offset": offset,
        "limit": limit,
        "total": total,
    }


@router.get("/{row_id}")
async def get_history_by_id(row_id: int) -> dict[str, Any]:
    item = get_history_item(row_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History item not found")
    return item.to_dict()
