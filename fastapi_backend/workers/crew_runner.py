import os
import threading

from deep_research_team.crew import DeepResearchCrew
from deep_research_team.settings import report_path_for
from deep_research_team.tools.db_utils import save_history, update_history
from deep_research_team.tools.progress import (
    _STEPS,
    get_status,
    reset_progress,
    set_crew_error,
    set_crew_result,
)

from fastapi_backend.workers.progress_store import update_task

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("LITELLM_DROP_PARAMS", "true")


def _poll_progress(task_id: str, stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        agent, completed = get_status()
        total = len(_STEPS)
        pct = round((len(completed) / total) * 100, 1) if total else 0.0
        update_task(task_id, current_agent=agent, completed_tasks=list(completed), pct=pct)
        stop_event.wait(0.5)


def run_crew_task(task_id: str, business_field: str) -> None:
    row_id: int | None = None
    stop_poller = threading.Event()

    try:
        reset_progress()
        row_id = save_history(business_field, "running")
        update_task(task_id, status="running", row_id=row_id)

        file_path = report_path_for(row_id)
        crew = DeepResearchCrew()
        crew.report_path = str(file_path)

        poller = threading.Thread(target=_poll_progress, args=(task_id, stop_poller), daemon=True)
        poller.start()

        result = crew.crew().kickoff(inputs={"business_field": business_field})
        set_crew_result(result)

        stop_poller.set()
        agent, completed = get_status()
        update_task(
            task_id,
            status="completed",
            current_agent=None,
            completed_tasks=list(completed),
            pct=100.0,
            report_path=str(file_path),
        )
        update_history(row_id, "completed", report_path=str(file_path))

    except Exception as e:
        stop_poller.set()
        set_crew_error(str(e))
        update_task(task_id, status="failed", error=str(e))
        if row_id is not None:
            update_history(row_id, "failed", error=str(e))
