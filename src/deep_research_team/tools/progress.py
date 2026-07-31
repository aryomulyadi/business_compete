import logging
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)

_STEPS = [
    ("Researcher", "Mengumpulkan data kompetitor"),
    ("Analyst", "Menganalisis SWOT, Five Forces, PESTEL"),
    ("Writer", "Menulis laporan akhir"),
]

_completed_tasks: list[str] = []
_current_agent: str | None = None
_start_time: float | None = None

_crew_result: Any = None
_crew_error: str | None = None
_thread_running: bool = False
_lock = threading.Lock()


def reset_progress() -> None:
    with _lock:
        _completed_tasks.clear()
        global _current_agent, _start_time
        _current_agent = None
        _start_time = None
        global _crew_result, _crew_error, _thread_running
        _crew_result = None
        _crew_error = None
        _thread_running = False


def set_crew_result(result: Any) -> None:
    with _lock:
        global _crew_result, _thread_running
        _crew_result = result
        _thread_running = False


def set_crew_error(error: str) -> None:
    with _lock:
        global _crew_error, _thread_running
        _crew_error = error
        _thread_running = False


def get_crew_result() -> Any:
    with _lock:
        return _crew_result


def get_crew_error() -> str | None:
    with _lock:
        return _crew_error


def is_thread_running() -> bool:
    with _lock:
        return _thread_running


def set_thread_running(val: bool) -> None:
    with _lock:
        global _thread_running
        _thread_running = val


def get_status() -> tuple[str | None, list[str]]:
    with _lock:
        return _current_agent, list(_completed_tasks)


class ProgressCallback:
    """Minimal callback for CrewAI step notification (no Rich output)."""

    def __call__(self, step: Any) -> None:
        try:
            agent_name = (
                getattr(getattr(step, "agent", None), "role", None)
                or getattr(step, "agent_name", None)
                or getattr(getattr(step, "task", None), "agent_name", None)
                or "Unknown"
            )
            with _lock:
                global _current_agent, _start_time
                if _start_time is None:
                    _start_time = time.time()
                for name, _ in _STEPS:
                    if name.lower() in agent_name.lower():
                        if name not in _completed_tasks and _current_agent != name:
                            if _current_agent and _current_agent not in _completed_tasks:
                                _completed_tasks.append(_current_agent)
                            _current_agent = name
                        break
        except Exception as exc:
            logger.debug("ProgressCallback error: %s", exc)

    def finalize(self) -> None:
        with _lock:
            global _current_agent
            if _current_agent and _current_agent not in _completed_tasks:
                _completed_tasks.append(_current_agent)
            _current_agent = None


def progress_step_handler(step: Any) -> None:
    ProgressCallback()(step)
