import time
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
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


def reset_progress() -> None:
    _completed_tasks.clear()
    global _current_agent, _start_time
    _current_agent = None
    _start_time = None


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


def progress_step_handler(step: Any) -> None:
    """Module-level callback for CrewAI step_callback (avoids Pydantic serialization warning)."""
    ProgressCallback()(step)
