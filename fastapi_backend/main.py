import os
import sys
import io
import warnings

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from deep_research_team.settings import ENV_VARS, setup_logging, validate_env
from deep_research_team.tools.db_utils import init_db

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)
app.include_router(reports_router)
app.include_router(branding_router)
app.include_router(history_router)


@app.on_event("startup")
async def startup() -> None:
    init_db()


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "bizcomp-ai-api"}
