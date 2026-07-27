"""Run this as a long-lived worker (Railway/Render), never as a Vercel Function."""
import time

from deep_research_team.tools.db_utils import claim_next_task, init_db
from fastapi_backend.workers.crew_runner import run_crew_task


def main() -> None:
    init_db()
    while True:
        task = claim_next_task()
        if task is None:
            time.sleep(2)
            continue
        run_crew_task(task["task_id"], task["field"], int(task["row_id"]))


if __name__ == "__main__":
    main()
