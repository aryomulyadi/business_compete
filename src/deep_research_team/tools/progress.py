import threading
import time
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

console = Console()

_STEPS = [
    ("Researcher", "Mengumpulkan data kompetitor"),
    ("Analyst", "Menganalisis SWOT, Five Forces, PESTEL"),
    ("Writer", "Menulis laporan akhir"),
]

_AGENT_ICONS = {
    "Researcher": "🔍",
    "Analyst": "📊",
    "Writer": "✍️",
}

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


def _build_progress() -> Progress:
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )
    total = len(_STEPS)
    done = len(_completed_tasks)
    task = progress.add_task("[cyan]Total Progress", total=total)
    progress.update(task, completed=done)
    return progress


def _build_status_table() -> Table:
    table = Table.grid(padding=(0, 2))
    for name, desc in _STEPS:
        icon = _AGENT_ICONS.get(name, "•")
        if name in _completed_tasks:
            status = "✅ Selesai"
        elif name == _current_agent:
            status = f"⏳ {desc}..."
        else:
            status = "⏸️ Menunggu"
        table.add_row(f"{icon} {name}", status)
    return table


def _build_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(Panel(_build_progress(), title="Progress"), size=3),
        Layout(Panel(_build_status_table(), title="Status Agent")),
    )
    return layout


class ProgressCallback:
    """CrewAI step callback to track agent progress in real-time using Rich."""

    def __call__(self, step: Any) -> None:
        agent_name = getattr(getattr(step, "agent", None), "role", None) or getattr(
            step, "agent_name", None
        ) or getattr(getattr(step, "task", None), "agent_name", None) or "Unknown"

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

        console.clear()
        console.print(_build_layout())

    def finalize(self) -> None:
        global _current_agent
        if _current_agent and _current_agent not in _completed_tasks:
            _completed_tasks.append(_current_agent)
        _current_agent = None
        elapsed = time.time() - _start_time if _start_time else 0
        console.clear()
        console.print(
            Panel(
                Text("✅ Semua agent selesai!", justify="center", style="bold green")
                + Text(f"\n⏱️ Total waktu: {elapsed:.1f} detik", justify="center")
            )
        )


def set_crew_result(result: Any) -> None:
    """Set crew result (called from background thread)."""
    with _lock:
        global _crew_result, _thread_running
        _crew_result = result
        _thread_running = False


def set_crew_error(error: str) -> None:
    """Set crew error (called from background thread)."""
    with _lock:
        global _crew_error, _thread_running
        _crew_error = error
        _thread_running = False


def get_crew_result() -> Any:
    """Get crew result (thread-safe, called from main thread)."""
    with _lock:
        return _crew_result


def get_crew_error() -> str | None:
    """Get crew error (thread-safe)."""
    with _lock:
        return _crew_error


def is_thread_running() -> bool:
    """Check if crew thread is still running (thread-safe)."""
    with _lock:
        return _thread_running


def set_thread_running(val: bool) -> None:
    """Set running flag (thread-safe)."""
    with _lock:
        global _thread_running
        _thread_running = val


def get_status() -> tuple[str | None, list[str]]:
    """Return (current_agent, completed_tasks) for polling by external UI (e.g. Streamlit)."""
    with _lock:
        return _current_agent, list(_completed_tasks)


def progress_step_handler(step: Any) -> None:
    """Module-level callback for CrewAI step_callback (avoids Pydantic serialization warning)."""
    ProgressCallback()(step)
