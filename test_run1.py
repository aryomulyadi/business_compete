"""Run 1 test execution of E2E eval."""
import os
import sys
import time
import uuid
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LITELLM_DROP_PARAMS"] = "true"
os.environ["LITELLM_LOG"] = "ERROR"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["CREWAI_DESERIALIZE_CALLBACKS"] = "true"

sys.path.insert(0, str(Path(__file__).parent))

# Load .env.local
env_file = Path(__file__).parent / ".env.local"
for line in env_file.read_text("utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    k, v = k.strip(), v.strip().strip("\"'")
    if v and not os.environ.get(k):
        os.environ[k] = v

from deep_research_team.tools.db_utils import get_history_row, save_history
from fastapi_backend.workers.crew_runner import run_crew_task

task_id = str(uuid.uuid4())
row_id = save_history("E-commerce Skincare Lokal", "pending")
# Create task in analysis_tasks too
from deep_research_team.tools.db_utils import _connect, _execute, _now
conn = _connect()
_execute(conn, "INSERT INTO analysis_tasks (task_id, business_field, status, row_id, created_at, updated_at) VALUES (?, ?, 'pending', ?, ?, ?)",
         (task_id, "E-commerce Skincare Lokal", row_id, _now(), _now()))
conn.commit()
conn.close()

print(f"Task {task_id} row_id={row_id}")

t0 = time.time()
try:
    run_crew_task(task_id, "E-commerce Skincare Lokal", row_id)
    elapsed = time.time() - t0
    row = get_history_row(row_id)
    if row:
        print(f"Done in {elapsed:.0f}s: status={row['status']}, path={str(row.get('report_path',''))[:80]}")
    else:
        print(f"Done in {elapsed:.0f}s: row not found")
except Exception as e:
    import traceback
    elapsed = time.time() - t0
    traceback.print_exc()
    print(f"FAILED in {elapsed:.0f}s: {type(e).__name__}: {str(e)[:500]}")
