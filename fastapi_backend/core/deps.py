from pathlib import Path

from fastapi import HTTPException, status

from deep_research_team.settings import REPORT_FILE
from deep_research_team.tools.db_utils import get_history_row


def get_report_path(row_id: int) -> Path:
    row = get_history_row(row_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History item not found")
    rp = row.get("report_path")
    if rp and Path(rp).exists():
        return Path(rp)
    if REPORT_FILE.exists():
        return REPORT_FILE
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found")
