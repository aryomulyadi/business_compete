import os
import sys
import io
import threading
import time
import warnings

from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from deep_research_team.settings import ENV_VARS, setup_logging, validate_env
from deep_research_team.tools.db_utils import claim_next_task, init_db
from fastapi_backend.workers.crew_runner import run_crew_task

from fastapi_backend.api.analysis import router as analysis_router
from fastapi_backend.api.reports import router as reports_router
from fastapi_backend.api.branding import router as branding_router
from fastapi_backend.api.history import router as history_router

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("LITELLM_DROP_PARAMS", "true")

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

load_dotenv()
load_dotenv(".env.local", override=True)
for var in ENV_VARS:
    os.environ[var] = os.getenv(var, "")

logger = setup_logging(__name__)

missing = validate_env()
for m in missing:
    logger.warning("Missing API key: %s", m)

app = FastAPI(
    title="BizComp AI API",
    version="0.1.0",
    description="Navigasi Arah Bisnis, Kuasai Peta Persaingan.",
)

cors_origins = os.getenv(
    "CORS_ORIGINS",
    os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:3000,http://127.0.0.1:3000"),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)
app.include_router(reports_router)
app.include_router(branding_router)
app.include_router(history_router)


def _run_worker() -> None:
    """Worker daemon: polls DB for pending analysis tasks and executes them."""
    while True:
        try:
            task = claim_next_task()
            if task is None:
                time.sleep(2)
                continue
            logger.info("Worker picked up task %s: %s", task["task_id"], task["field"])
            run_crew_task(task["task_id"], task["field"], int(task["row_id"]))
        except Exception as exc:
            logger.error("Worker error: %s", exc, exc_info=True)
            time.sleep(5)


@app.on_event("startup")
async def startup() -> None:
    if os.getenv("VERCEL") == "1" and not os.getenv("DATABASE_URL"):
        logger.warning("DATABASE_URL not set — using SQLite fallback")
    init_db()
    logger.info("Worker daemon starting (LLM_PROVIDER=%s)", os.getenv("LLM_PROVIDER"))
    t = threading.Thread(target=_run_worker, daemon=True)
    t.start()
    logger.info("Worker daemon started")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "bizcomp-ai-api"}
