#!/usr/bin/env python

import atexit
import os
from pathlib import Path
import re
import shutil
import threading
import time

from dotenv import load_dotenv
import streamlit as st

from deep_research_team.settings import ENV_VARS, REPORT_FILE, report_path_for, setup_logging, validate_env
from deep_research_team.crew import DeepResearchCrew
from deep_research_team.page_utils import render_sidebar
from deep_research_team.tools.db_utils import init_db, save_history, update_history
from deep_research_team.tools.progress import (
    _STEPS as AGENT_STEPS,
    get_crew_error,
    get_crew_result,
    get_status,
    is_thread_running,
    reset_progress,
    set_crew_error,
    set_crew_result,
    set_thread_running,
)
from deep_research_team.tools.search_tool import check_serper_api_key, filter_fake_urls_from_report

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("LITELLM_DROP_PARAMS", "true")
load_dotenv()
load_dotenv(".env.local", override=True)
for var in ENV_VARS:
    os.environ[var] = os.getenv(var, "")

logger = setup_logging(__name__)

missing = validate_env()
if missing:
    for m in missing:
        logger.warning("Missing API key: %s", m)
    if not os.getenv("SERPER_API_KEY"):
        st.warning("SERPER_API_KEY tidak diatur. Cari API key di https://serper.dev")

_start_lock = threading.Lock()

st.set_page_config(
    page_title="Deep Research Team",
    page_icon="static/favicon.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_sidebar()

init_db()

def _cleanup_on_exit() -> None:
    from deep_research_team.tools.progress import get_crew_result, set_crew_error, set_thread_running
    set_thread_running(False)
    if get_crew_result() is None:
        set_crew_error("Analisis terputus: server dimatikan.")

atexit.register(_cleanup_on_exit)

ok, msg = check_serper_api_key()
if not ok:
    st.warning(f"Serper API: {msg}. Pencarian mungkin gagal dan data bisa tidak akurat.")

st.title("Deep Research Team")
st.markdown(
    '<p style="margin-top: -0.5rem; opacity: 0.6; font-size: 0.95rem;">'
    "Analisis kompetitor bisnis dengan AI - SWOT, Five Forces, PESTEL</p>",
    unsafe_allow_html=True,
)

col_input, col_btn = st.columns([3, 1])
with col_input:
    business_field = st.text_input(
        "Bidang bisnis yang ingin dianalisis",
        placeholder="Contoh: E-commerce Fesyen, SaaS HR, Fintech Indonesia",
        label_visibility="collapsed",
    )
with col_btn:
    run_clicked = st.button(
        "Mulai Analisis", type="primary", disabled=not business_field or is_thread_running(), use_container_width=True
    )

status_placeholder = st.empty()
progress_placeholder = st.empty()

if run_clicked and business_field:
    field_clean = business_field.strip()[:200]
    if not field_clean:
        status_placeholder.error("Bidang bisnis tidak boleh kosong.")
        st.stop()
    if len(field_clean) < 10:
        status_placeholder.warning("Bidang bisnis terlalu pendek (min. 10 karakter).")
        st.stop()

    with _start_lock:
        if is_thread_running():
            st.warning("Analisis sedang berjalan, harap tunggu...")
            st.stop()

        reset_progress()
        st.session_state._poll_count = 0
        row_id = save_history(field_clean, "running")
        st.session_state.row_id = row_id
        st.session_state.field_clean = field_clean
        set_thread_running(True)
        st.toast(f"Analisis {field_clean} dimulai!", icon="🚀")

        def _target() -> None:
            try:
                crew = DeepResearchCrew()
                file_path = report_path_for(row_id)
                crew.report_path = str(file_path)
                result = crew.crew().kickoff(
                    inputs={"business_field": field_clean}
                )
                set_crew_result(result)
            except Exception as e:
                set_crew_error(str(e))

        threading.Thread(target=_target, daemon=True).start()
        st.rerun()

if is_thread_running():
    field_clean = st.session_state.get("field_clean", "")
    if not field_clean:
        status_placeholder.empty()
        progress_placeholder.empty()
        st.rerun()

    poll_count = st.session_state.get("_poll_count", 0) + 1
    st.session_state._poll_count = poll_count
    if poll_count > 600:
        set_crew_error("Analisis melebihi batas waktu (5 menit). Coba lagi.")
        st.rerun()

    current_agent, completed_tasks = get_status()
    done = len(completed_tasks)
    total = len(AGENT_STEPS)
    pct = int((done / total) * 90) + 10 if total else 10

    if current_agent:
        progress_placeholder.progress(
            min(pct, 99), text=f"{current_agent} - {done}/{total} selesai"
        )
    else:
        progress_placeholder.progress(
            min(pct, 99), text=f"Menganalisis {field_clean}..."
        )

    status_placeholder.info(f"Menganalisis {field_clean}...")
    time.sleep(0.5)
    st.rerun()

elif get_crew_error() is not None:
    row_id = st.session_state.get("row_id")
    field_clean = st.session_state.get("field_clean", "")
    error_msg = get_crew_error()
    if row_id is not None:
        update_history(row_id, "failed", error=error_msg)
    status_placeholder.error(f"Gagal: {error_msg}")
    progress_placeholder.progress(0, text="Gagal")
    if st.button("Coba Lagi", type="secondary"):
        for key in ("row_id", "field_clean"):
            st.session_state.pop(key, None)
        st.rerun()

elif get_crew_result() is not None:
    row_id = st.session_state.get("row_id")
    field_clean = st.session_state.get("field_clean", "")
    file_path = str(report_path_for(row_id)) if row_id else None

    if row_id is not None and file_path is not None:
        update_history(row_id, "completed", report_path=file_path)

    progress_placeholder.progress(100, text="Selesai!")
    status_placeholder.success(f"Analisis {field_clean} selesai!")
    st.toast(f"Analisis {field_clean} selesai!", icon="✅")

    st.divider()

    report = Path(file_path) if file_path else REPORT_FILE
    if not report.exists():
        st.error("File laporan tidak ditemukan!")
        if row_id is not None:
            update_history(row_id, "failed", error="File tidak ditemukan")
        st.stop()

    with open(report, "r", encoding="utf-8") as f:
        report_content = f.read()

    if len(report_content.strip()) < 50:
        st.warning(
            f"Report terlalu pendek ({len(report_content.strip())} chars) - "
            "analisis mungkin gagal."
        )
        if row_id is not None:
            update_history(row_id, "failed", error="Report terlalu pendek")
        status_placeholder.error("Analisis gagal - output tidak mencukupi.")
        st.stop()

    if report.exists():
        shutil.copy2(report, report.with_suffix(".bak.md"))
    report_content = filter_fake_urls_from_report(report_content)
    report_content = re.sub(
        r'^```(?:markdown)?\s*\n(.*?)\n```\s*$',
        r'\1',
        report_content.strip(),
        count=1,
        flags=re.DOTALL,
    )
    with open(report, "w", encoding="utf-8") as f:
        f.write(report_content)

    if st.button("Lihat Laporan", type="primary", use_container_width=True):
        st.switch_page("pages/1_Report.py")
