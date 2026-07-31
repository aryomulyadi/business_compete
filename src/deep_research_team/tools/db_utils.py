"""Durable persistence for local development and production workers.

SQLite is intentionally supported only when DATABASE_URL is unset. Production
deployments must use a PostgreSQL URL so API and worker instances share state.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from deep_research_team import settings


def _is_postgres() -> bool:
    return os.getenv("DATABASE_URL", "").startswith(("postgres://", "postgresql://"))


def _connect() -> Any:
    if _is_postgres():
        try:
            import psycopg
        except ImportError as exc:  # pragma: no cover - deployment configuration error
            raise RuntimeError("PostgreSQL requires psycopg. Install the production dependencies.") from exc
        return psycopg.connect(os.environ["DATABASE_URL"])
    default_db = "/tmp/bizcomp.db" if os.getenv("VERCEL") == "1" else str(settings.DB_PATH)
    db_path = Path(os.getenv("VERCEL_DB_PATH", default_db))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path))


def _execute(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> Any:
    if _is_postgres():
        sql = sql.replace("?", "%s")
    return conn.execute(sql, params)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    conn = _connect()
    try:
        if _is_postgres():
            statements = [
                "CREATE TABLE IF NOT EXISTS history (id BIGSERIAL PRIMARY KEY, business_field TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'running', created_at TEXT NOT NULL, report_path TEXT, error TEXT)",
                "CREATE TABLE IF NOT EXISTS logo_history (id BIGSERIAL PRIMARY KEY, history_row_id BIGINT NOT NULL REFERENCES history(id), brand_name TEXT NOT NULL, concept TEXT, svg TEXT, png_path TEXT, style TEXT, created_at TEXT NOT NULL)",
                "CREATE TABLE IF NOT EXISTS analysis_tasks (task_id TEXT PRIMARY KEY, business_field TEXT NOT NULL, status TEXT NOT NULL, current_agent TEXT, completed_tasks TEXT NOT NULL DEFAULT '[]', pct DOUBLE PRECISION NOT NULL DEFAULT 0, error TEXT, row_id BIGINT REFERENCES history(id), report_path TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
            ]
        else:
            statements = [
                "CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, business_field TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'running', created_at TEXT NOT NULL, report_path TEXT, error TEXT)",
                "CREATE TABLE IF NOT EXISTS logo_history (id INTEGER PRIMARY KEY AUTOINCREMENT, history_row_id INTEGER NOT NULL, brand_name TEXT NOT NULL, concept TEXT, svg TEXT, png_path TEXT, style TEXT, created_at TEXT NOT NULL, FOREIGN KEY (history_row_id) REFERENCES history(id))",
                "CREATE TABLE IF NOT EXISTS analysis_tasks (task_id TEXT PRIMARY KEY, business_field TEXT NOT NULL, status TEXT NOT NULL, current_agent TEXT, completed_tasks TEXT NOT NULL DEFAULT '[]', pct REAL NOT NULL DEFAULT 0, error TEXT, row_id INTEGER, report_path TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
            ]
        for statement in statements:
            _execute(conn, statement)
        _execute(conn, "UPDATE history SET status='failed', error=? WHERE status='running'", (f"Analisis terputus (restart). Stale since {_now()}",))
        conn.commit()
    finally:
        conn.close()


def _insert_returning_id(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> int:
    if _is_postgres():
        sql = sql.rstrip(";") + " RETURNING id"
    cursor = _execute(conn, sql, params)
    return cursor.fetchone()[0] if _is_postgres() else cursor.lastrowid


def _migrate_add_brand_names() -> None:
    conn = _connect()
    try:
        if _is_postgres():
            _execute(conn, "ALTER TABLE history ADD COLUMN IF NOT EXISTS brand_names TEXT")
        else:
            try:
                _execute(conn, "ALTER TABLE history ADD COLUMN brand_names TEXT")
            except Exception:
                pass
        conn.commit()
    finally:
        conn.close()

_migrate_add_brand_names()


def update_history_brand_names(row_id: int, names: list[str]) -> None:
    conn = _connect()
    try:
        _execute(conn, "UPDATE history SET brand_names=? WHERE id=?", (json.dumps(names), row_id))
        conn.commit()
    finally:
        conn.close()


def get_branded_history_rows(offset: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
    conn = _connect()
    try:
        total = int(_execute(
            conn,
            "SELECT COUNT(*) FROM history WHERE status='completed' AND brand_names IS NOT NULL AND brand_names != '[]'",
        ).fetchone()[0])
        rows = _execute(
            conn,
            "SELECT id, business_field, status, created_at, brand_names FROM history WHERE status='completed' AND brand_names IS NOT NULL AND brand_names != '[]' ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    finally:
        conn.close()
    branded: list[dict[str, Any]] = []
    for r in rows:
        names = json.loads(r[4]) if isinstance(r[4], str) else r[4] or []
        branded.append({
            "row_id": r[0],
            "field": r[1],
            "created_at": r[3],
            "brand_names": names,
        })
    return branded, total


def save_history(field: str, status: str, report_path: Optional[str] = None, error: Optional[str] = None) -> int:
    conn = _connect()
    try:
        row_id = _insert_returning_id(conn, "INSERT INTO history (business_field, status, created_at, report_path, error) VALUES (?, ?, ?, ?, ?)", (field, status, _now(), report_path, error))
        conn.commit()
        return int(row_id)
    finally:
        conn.close()


def update_history(row_id: int, status: str, report_path: Optional[str] = None, error: Optional[str] = None) -> None:
    conn = _connect()
    try:
        _execute(conn, "UPDATE history SET status=?, report_path=COALESCE(?, report_path), error=? WHERE id=?", (status, report_path, error, row_id))
        conn.commit()
    finally:
        conn.close()


def get_history_row(row_id: int) -> Optional[dict[str, Any]]:
    conn = _connect()
    try:
        row = _execute(conn, "SELECT id, business_field, status, created_at, report_path, error FROM history WHERE id=?", (row_id,)).fetchone()
    finally:
        conn.close()
    return None if row is None else {"id": row[0], "field": row[1], "status": row[2], "created_at": row[3], "report_path": row[4], "error": row[5]}


def save_logo(history_row_id: int, brand_name: str, concept: str = "", svg: str = "", png_path: str = "", style: str = "") -> int:
    conn = _connect()
    try:
        row_id = _insert_returning_id(conn, "INSERT INTO logo_history (history_row_id, brand_name, concept, svg, png_path, style, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (history_row_id, brand_name, concept, svg, png_path, style, _now()))
        conn.commit()
        return int(row_id)
    finally:
        conn.close()


def get_logos(history_row_id: int) -> list[dict[str, Any]]:
    conn = _connect()
    try:
        rows = _execute(conn, "SELECT id, history_row_id, brand_name, concept, svg, png_path, style, created_at FROM logo_history WHERE history_row_id=? ORDER BY id DESC", (history_row_id,)).fetchall()
    finally:
        conn.close()
    return [{"id": r[0], "history_row_id": r[1], "brand_name": r[2], "concept": r[3], "svg": r[4], "png_path": r[5], "style": r[6], "created_at": r[7]} for r in rows]


def get_logo(logo_id: int) -> Optional[dict[str, Any]]:
    conn = _connect()
    try:
        row = _execute(conn, "SELECT id, history_row_id, brand_name, concept, svg, png_path, style, created_at FROM logo_history WHERE id=?", (logo_id,)).fetchone()
    finally:
        conn.close()
    return None if row is None else {"id": row[0], "history_row_id": row[1], "brand_name": row[2], "concept": row[3], "svg": row[4], "png_path": row[5], "style": row[6], "created_at": row[7]}


def get_history(limit: int = 20) -> list[dict[str, Any]]:
    conn = _connect()
    try:
        rows = _execute(conn, "SELECT id, business_field, status, created_at, report_path, error FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    finally:
        conn.close()
    return [{"id": r[0], "field": r[1], "status": r[2], "created_at": r[3], "report_path": r[4], "error": r[5]} for r in rows]


def list_history_rows(limit: int = 50, offset: int = 0, search: Optional[str] = None) -> list[dict[str, Any]]:
    conn = _connect()
    try:
        query = "SELECT id, business_field, status, created_at, report_path, error FROM history"
        params: list[Any] = []
        if search:
            query += " WHERE business_field LIKE ?"
            params.append(f"%{search}%")
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = _execute(conn, query, tuple(params)).fetchall()
    finally:
        conn.close()
    return [{"id": r[0], "field": r[1], "status": r[2], "created_at": r[3], "report_path": r[4], "error": r[5]} for r in rows]


def count_history_rows(search: Optional[str] = None) -> int:
    conn = _connect()
    try:
        query = "SELECT COUNT(*) FROM history"
        params: tuple[Any, ...] = ()
        if search:
            query += " WHERE business_field LIKE ?"
            params = (f"%{search}%",)
        return int(_execute(conn, query, params).fetchone()[0])
    finally:
        conn.close()


def create_task(task_id: str, business_field: str, row_id: int) -> None:
    now = _now()
    conn = _connect()
    try:
        _execute(conn, "INSERT INTO analysis_tasks (task_id, business_field, status, row_id, created_at, updated_at) VALUES (?, ?, 'pending', ?, ?, ?)", (task_id, business_field, row_id, now, now))
        conn.commit()
    finally:
        conn.close()


def get_task(task_id: str) -> Optional[dict[str, Any]]:
    conn = _connect()
    try:
        row = _execute(conn, "SELECT task_id, business_field, status, current_agent, completed_tasks, pct, error, row_id, report_path FROM analysis_tasks WHERE task_id=?", (task_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {"task_id": row[0], "field": row[1], "status": row[2], "current_agent": row[3], "completed_tasks": json.loads(row[4] or "[]"), "pct": row[5], "error": row[6], "row_id": row[7], "report_path": row[8]}


def update_task(task_id: str, **values: Any) -> None:
    allowed = {"status", "current_agent", "completed_tasks", "pct", "error", "row_id", "report_path"}
    clean = {key: (json.dumps(value) if key == "completed_tasks" else value) for key, value in values.items() if key in allowed}
    if not clean:
        return
    assignments = ", ".join(f"{key}=?" for key in clean) + ", updated_at=?"
    conn = _connect()
    try:
        _execute(conn, f"UPDATE analysis_tasks SET {assignments} WHERE task_id=?", (*clean.values(), _now(), task_id))
        conn.commit()
    finally:
        conn.close()


def claim_next_task() -> Optional[dict[str, Any]]:
    """Atomically reserve one pending task for a worker."""
    conn = _connect()
    try:
        if _is_postgres():
            row = _execute(conn, "UPDATE analysis_tasks SET status='running', updated_at=? WHERE task_id = (SELECT task_id FROM analysis_tasks WHERE status='pending' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING task_id, business_field, row_id", (_now(),)).fetchone()
        else:
            conn.execute("BEGIN IMMEDIATE")
            row = _execute(conn, "SELECT task_id, business_field, row_id FROM analysis_tasks WHERE status='pending' ORDER BY created_at LIMIT 1").fetchone()
            if row:
                _execute(conn, "UPDATE analysis_tasks SET status='running', updated_at=? WHERE task_id=?", (_now(), row[0]))
        conn.commit()
    finally:
        conn.close()
    return None if row is None else {"task_id": row[0], "field": row[1], "row_id": row[2]}
