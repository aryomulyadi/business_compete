from deep_research_team.tools.db_utils import create_task, get_task, init_db, save_history, update_task


def test_task_progress_is_persisted(temp_output_dir):
    init_db()
    row_id = save_history("SaaS akuntansi", "pending")
    create_task("task-1", "SaaS akuntansi", row_id)
    update_task("task-1", status="running", current_agent="Researcher", completed_tasks=["Setup"], pct=25.0)

    task = get_task("task-1")

    assert task is not None
    assert task["status"] == "running"
    assert task["row_id"] == row_id
    assert task["completed_tasks"] == ["Setup"]
    assert task["pct"] == 25.0
