"""Database-backed task state shared by API and worker deployments."""
from dataclasses import dataclass
from typing import Any, Optional

from deep_research_team.tools import db_utils


@dataclass
class TaskProgress:
    task_id: str
    status: str
    business_field: str
    current_agent: Optional[str] = None
    completed_tasks: list[str] | None = None
    pct: float = 0.0
    error: Optional[str] = None
    row_id: Optional[int] = None
    report_path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {"task_id": self.task_id, "status": self.status, "field": self.business_field, "current_agent": self.current_agent, "completed_tasks": self.completed_tasks or [], "pct": self.pct, "error": self.error, "row_id": self.row_id, "report_path": self.report_path}


def create_task(task_id: str, business_field: str, row_id: int) -> TaskProgress:
    db_utils.create_task(task_id, business_field, row_id)
    return TaskProgress(task_id, "pending", business_field, row_id=row_id)


def get_task(task_id: str) -> Optional[TaskProgress]:
    row = db_utils.get_task(task_id)
    return None if row is None else TaskProgress(row["task_id"], row["status"], row["field"], row["current_agent"], row["completed_tasks"], float(row["pct"] or 0), row["error"], row["row_id"], row["report_path"])


def update_task(task_id: str, **kwargs: Any) -> Optional[TaskProgress]:
    db_utils.update_task(task_id, **kwargs)
    return get_task(task_id)
