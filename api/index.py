"""Vercel Python Function entry point."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastapi_backend.main import app

__all__ = ["app"]
