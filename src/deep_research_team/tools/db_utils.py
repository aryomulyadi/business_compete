import sqlite3
from datetime import datetime
from typing import Any, Optional

from deep_research_team.settings import DB_PATH


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_field TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'running',
            created_at TEXT NOT NULL,
            report_path TEXT,
            error TEXT
        )
    """
    )
    conn.commit()
    conn.close()


def _prune_history(max_rows: int = 100) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY id DESC LIMIT ?)",
        (max_rows,),
    )
    conn.commit()
    conn.close()


def save_history(field: str, status: str, report_path: Optional[str] = None, error: Optional[str] = None) -> int:
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute(
        "INSERT INTO history (business_field, status, created_at, report_path, error) VALUES (?, ?, ?, ?, ?)",
        (field, status, datetime.now().isoformat(), report_path, error),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    _prune_history()
    return row_id


def update_history(row_id: int, status: str, report_path: Optional[str] = None, error: Optional[str] = None) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "UPDATE history SET status=?, report_path=COALESCE(?, report_path), error=? WHERE id=?",
        (status, report_path, error, row_id),
    )
    conn.commit()
    conn.close()


def get_history_row(row_id: int) -> Optional[dict[str, Any]]:
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute(
        "SELECT id, business_field, status, created_at, report_path, error FROM history WHERE id=?",
        (row_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return {"id": row[0], "field": row[1], "status": row[2],
            "created_at": row[3], "report_path": row[4], "error": row[5]}


def get_history(limit: int = 20) -> list[dict[str, Any]]:
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT id, business_field, status, created_at, report_path, error FROM history ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "field": r[1], "status": r[2],
         "created_at": r[3], "report_path": r[4], "error": r[5]}
        for r in rows
    ]
