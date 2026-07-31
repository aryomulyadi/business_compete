import os
import threading
import tempfile
from pathlib import Path

from deep_research_team.crew import DeepResearchCrew
from deep_research_team.backend.report_service import get_brand_names
from deep_research_team.tools.db_utils import update_history, update_history_brand_names
from deep_research_team.tools.llm_utils import clear_llm_cache
from deep_research_team.tools.search_tool import clear_session_cache
from deep_research_team.tools.progress import (
    _STEPS,
    get_status,
    reset_progress,
    set_crew_error,
    set_crew_result,
)
from deep_research_team.tools.storage import upload_bytes

from fastapi_backend.workers.progress_store import update_task
from deep_research_team.settings import setup_logging

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("LITELLM_DROP_PARAMS", "true")

logger = setup_logging(__name__)


def _poll_progress(task_id: str, stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        agent, completed = get_status()
        total = len(_STEPS)
        pct = round((len(completed) / total) * 100, 1) if total else 0.0
        update_task(task_id, current_agent=agent, completed_tasks=list(completed), pct=pct)
        stop_event.wait(0.5)


def run_crew_task(task_id: str, business_field: str, row_id: int) -> None:
    stop_poller = threading.Event()

    try:
        reset_progress()
        clear_llm_cache()
        clear_session_cache()
        update_history(row_id, "running")
        update_task(task_id, row_id=row_id)

        with tempfile.TemporaryDirectory(prefix="bizcomp-") as temp_dir:
            file_path = Path(temp_dir) / f"laporan_{row_id}.md"
            crew = DeepResearchCrew()
            crew.report_path = str(file_path)

            poller = threading.Thread(target=_poll_progress, args=(task_id, stop_poller), daemon=True)
            poller.start()

            result = crew.crew().kickoff(inputs={"business_field": business_field})
            set_crew_result(result)
            report_content = file_path.read_bytes()
            report_url = upload_bytes(f"reports/{row_id}.md", report_content, "text/markdown; charset=utf-8")
            try:
                names = get_brand_names(report_content.decode("utf-8"))
                if names:
                    update_history_brand_names(row_id, names)
            except Exception as exc:
                logger.warning("Failed to save brand_names for row %d: %s", row_id, exc)

        stop_poller.set()
        agent, completed = get_status()
        update_task(
            task_id,
            status="completed",
            current_agent=None,
            completed_tasks=list(completed),
            pct=100.0,
            report_path=report_url,
        )
        update_history(row_id, "completed", report_path=report_url)

    except Exception as e:
        stop_poller.set()
        set_crew_error(str(e))
        update_task(task_id, status="failed", error=str(e))
        if row_id is not None:
            update_history(row_id, "failed", error=str(e))
