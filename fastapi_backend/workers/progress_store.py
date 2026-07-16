import threading
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TaskProgress:
    task_id: str
    status: str = "pending"
    business_field: str = ""
    current_agent: Optional[str] = None
    completed_tasks: list[str] = field(default_factory=list)
    pct: float = 0.0
    error: Optional[str] = None
    row_id: Optional[int] = None
    report_path: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "field": self.business_field,
            "current_agent": self.current_agent,
            "completed_tasks": list(self.completed_tasks),
            "pct": self.pct,
            "error": self.error,
            "row_id": self.row_id,
            "report_path": self.report_path,
        }


_store: dict[str, TaskProgress] = {}
_lock = threading.Lock()
_MAX_TASKS = 500


def create_task(task_id: str, business_field: str) -> TaskProgress:
    with _lock:
        if len(_store) >= _MAX_TASKS:
            oldest = min(_store.keys(), key=lambda k: _store[k].created_at)
            del _store[oldest]
        tp = TaskProgress(task_id=task_id, business_field=business_field, status="pending")
        _store[task_id] = tp
        return tp


def get_task(task_id: str) -> Optional[TaskProgress]:
    with _lock:
        return _store.get(task_id)


def update_task(task_id: str, **kwargs: Any) -> Optional[TaskProgress]:
    with _lock:
        tp = _store.get(task_id)
        if tp is None:
            return None
        for k, v in kwargs.items():
            setattr(tp, k, v)
        return tp
