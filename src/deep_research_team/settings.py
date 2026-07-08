from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent

OUTPUT_DIR: Final[Path] = PROJECT_ROOT / "output"
REPORT_FILE: Final[Path] = OUTPUT_DIR / "laporan_analisis_kompetitor.md"
CACHE_DIR: Final[Path] = OUTPUT_DIR / "cache"
DB_PATH: Final[Path] = OUTPUT_DIR / "history.db"

AGENTS_CONFIG: Final[str] = "config/agents.yaml"
TASKS_CONFIG: Final[str] = "config/tasks.yaml"

RESEARCHER_MAX_TOKENS: Final[int] = 4096
ANALYST_MAX_TOKENS: Final[int] = 8192
WRITER_MAX_TOKENS: Final[int] = 16384

RESEARCHER_MAX_ITER: Final[int] = 8
ANALYST_MAX_ITER: Final[int] = 3

SERPER_TIMEOUT: Final[int] = 10
URL_VALIDATE_TIMEOUT: Final[int] = 5
CACHE_TTL: Final[int] = 86400  # 24 jam

ENV_VARS: Final[list[str]] = [
    "GROQ_API_KEY",
    "SERPER_API_KEY",
    "DEEPSEEK_API_KEY",
    "MIMO_API_KEY",
    "GEMINI_API_KEY",
    "OMNIROUTE_API_KEY",
    "OMNIROUTE_BASE_URL",
    "OMNIROUTE_MODEL",
]

LLM_PROVIDER_DEFAULT: Final[str] = "mimo"

LOG_FORMAT: Final[str] = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(name: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name or __name__)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
