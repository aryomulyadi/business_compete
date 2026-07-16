import sqlite3
from typing import Optional

from deep_research_team.backend.models import HistoryItem
from deep_research_team.settings import DB_PATH
from deep_research_team.tools.db_utils import get_history_row, save_history, update_history


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
    conn = sqlite3.connect(str(DB_PATH))
    query = "SELECT id, business_field, status, created_at, report_path, error FROM history"
    params: list = []
    if search:
        query += " WHERE business_field LIKE ?"
        params.append(f"%{search}%")
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [HistoryItem.from_row(r) for r in rows]


def get_history_count(search: Optional[str] = None) -> int:
    conn = sqlite3.connect(str(DB_PATH))
    query = "SELECT COUNT(*) FROM history"
    params: list = []
    if search:
        query += " WHERE business_field LIKE ?"
        params.append(f"%{search}%")
    count = conn.execute(query, params).fetchone()[0]
    conn.close()
    return count
