from typing import Optional

from deep_research_team.backend.models import HistoryItem
from deep_research_team.tools.db_utils import count_history_rows, get_history_row, list_history_rows, save_history, update_history


def create_history(field: str, status: str = "running") -> int:
    return save_history(field, status)


def update_history_item(
    row_id: int,
    status: str,
    report_path: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    update_history(row_id, status, report_path, error)


def get_history_item(row_id: int) -> Optional[HistoryItem]:
    row = get_history_row(row_id)
    if row is None:
        return None
    return HistoryItem(
        id=row["id"],
        field=row["field"],
        status=row["status"],
        created_at=row["created_at"],
        report_path=row["report_path"],
        error=row["error"],
    )


def get_history_list(limit: int = 50, offset: int = 0, search: Optional[str] = None) -> list[HistoryItem]:
    return [HistoryItem(**row) for row in list_history_rows(limit, offset, search)]


def get_history_count(search: Optional[str] = None) -> int:
    return count_history_rows(search)
