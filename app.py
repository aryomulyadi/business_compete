#!/usr/bin/env python
"""Streamlit UI untuk Deep Research Team."""

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("LITELLM_DROP_PARAMS", "true")

from dotenv import load_dotenv

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")
os.environ["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY")
os.environ["MIMO_API_KEY"] = os.getenv("MIMO_API_KEY")

import streamlit as st
from deep_research_team.crew import DeepResearchCrew
from deep_research_team.tools.export_utils import md_to_html, md_to_pdf
from deep_research_team.tools.search_tool import check_serper_api_key, filter_fake_urls_from_report

st.set_page_config(
    page_title="Deep Research Team",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {padding-top: 1.5rem; padding-bottom: 0;}
h1 {font-size: 2rem !important; font-weight: 700 !important;
    letter-spacing: -0.5px !important;}
h2 {font-size: 1.3rem !important; font-weight: 600 !important;}
.stTextInput > div > div > input {font-size: 1rem;}
div[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem; padding-bottom: 1rem;
}
.history-card {
    border: 1px solid rgba(128,128,128,0.2);
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
    margin-bottom: 0.4rem;
    transition: border-color 0.2s;
}
.history-card:hover {border-color: rgba(128,128,128,0.5);}
.history-status {font-size: 0.75rem; opacity: 0.7;}
.history-field {font-weight: 600; font-size: 0.9rem;}
.history-date {font-size: 0.7rem; opacity: 0.5;}
.stButton > button {width: 100%; font-weight: 600;}
</style>
"""

st.markdown(_CSS, unsafe_allow_html=True)

DB_PATH = "output/history.db"
REPORT_FILE = "output/laporan_analisis_kompetitor.md"


def _strip_code_fence(text: str) -> str:
    """Remove surrounding ```markdown ... ``` fence if present."""
    return re.sub(
        r'^```(?:markdown)?\s*\n(.*?)\n```\s*$',
        r'\1',
        text.strip(),
        count=1,
        flags=re.DOTALL,
    )


def _init_db() -> None:
    Path("output").mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_field TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'running',
            created_at TEXT NOT NULL,
            report_path TEXT,
            error TEXT
        )
    """
    )
    conn.commit()
    conn.close()


def _save_history(field: str, status: str, report_path: str | None = None, error: str | None = None) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO history (business_field, status, created_at, report_path, error) VALUES (?, ?, ?, ?, ?)",
        (field, status, datetime.now().isoformat(), report_path, error),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def _update_history(row_id: int, status: str, report_path: str | None = None, error: str | None = None) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE history SET status=?, report_path=COALESCE(?, report_path), error=? WHERE id=?",
        (status, report_path, error, row_id),
    )
    conn.commit()
    conn.close()


def _get_history(limit: int = 20) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, business_field, status, created_at, report_path, error FROM history ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "field": r[1], "status": r[2],
         "created_at": r[3], "report_path": r[4], "error": r[5]}
        for r in rows
    ]


_init_db()

ok, msg = check_serper_api_key()
if not ok:
    st.warning(f"⚠️ Serper API: {msg}. Pencarian mungkin gagal dan data bisa tidak akurat.")

st.title("Deep Research Team")
st.markdown(
    '<p style="margin-top: -0.5rem; opacity: 0.6; font-size: 0.95rem;">'
    "Analisis kompetitor bisnis dengan AI — SWOT, Five Forces, PESTEL</p>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Riwayat Analisis")
    history = _get_history(10)
    if not history:
        st.caption("Belum ada riwayat.")
    else:
        for item in history:
            status_icon = {"completed": "✅", "running": "⏳", "failed": "❌"}.get(item["status"], "❓")
            st.markdown(
                f'<div class="history-card">'
                f'<div class="history-field">{status_icon} {item["field"]}</div>'
                f'<div class="history-status">{item["status"]}</div>'
                f'<div class="history-date">{item["created_at"][:16]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if item["report_path"] and Path(item["report_path"]).exists() and item["status"] == "completed":
                with open(item["report_path"], "r", encoding="utf-8") as f:
                    md_content = f.read()
                col_a, col_b = st.columns(2)
                with col_a:
                    st.download_button(
                        ".md", data=md_content,
                        file_name=Path(item["report_path"]).name,
                        mime="text/markdown",
                        key=f"side_md_{item['id']}",
                    )
                with col_b:
                    pdf_bytes = md_to_pdf(md_content)
                    if pdf_bytes:
                        st.download_button(
                            ".pdf", data=pdf_bytes,
                            file_name=Path(item["report_path"]).with_suffix(".pdf").name,
                            mime="application/pdf",
                            key=f"side_pdf_{item['id']}",
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
        "Mulai Analisis", type="primary", disabled=not business_field, use_container_width=True
    )

status_placeholder = st.empty()
progress_placeholder = st.empty()
result_placeholder = st.container()

if run_clicked and business_field:
    field_clean = business_field.strip()[:200]
    if not field_clean:
        status_placeholder.error("Bidang bisnis tidak boleh kosong.")
        st.stop()

    row_id = _save_history(field_clean, "running")

    progress_placeholder.progress(10, text="Mengumpulkan data kompetitor...")
    status_placeholder.info(f"Menganalisis **{field_clean}**...")

    try:
        result = DeepResearchCrew().crew().kickoff(
            inputs={"business_field": field_clean}
        )

        _update_history(row_id, "completed", report_path=REPORT_FILE)
        progress_placeholder.progress(100, text="Selesai!")
        status_placeholder.success(f"Analisis **{field_clean}** selesai!")

        with result_placeholder:
            st.divider()

            report_path = Path(REPORT_FILE)
            if report_path.exists():
                with open(report_path, "r", encoding="utf-8") as f:
                    report_content = f.read()

                report_content = filter_fake_urls_from_report(report_content)
                report_content = _strip_code_fence(report_content)
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(report_content)

                html_content = md_to_html(report_content)
                pdf_bytes = md_to_pdf(report_content)

                tab_preview, tab_download = st.tabs(["👁️ Preview", "📥 Download"])

                with tab_preview:
                    st.markdown(report_content)

                with tab_download:
                    dcols = st.columns(3)
                    with dcols[0]:
                        st.download_button(
                            "Download Markdown",
                            data=report_content,
                            file_name=report_path.name,
                            mime="text/markdown",
                            use_container_width=True,
                        )
                    with dcols[1]:
                        st.download_button(
                            "Download HTML",
                            data=html_content,
                            file_name=report_path.with_suffix(".html").name,
                            mime="text/html",
                            use_container_width=True,
                        )
                    with dcols[2]:
                        if pdf_bytes:
                            st.download_button(
                                "Download PDF",
                                data=pdf_bytes,
                                file_name=report_path.with_suffix(".pdf").name,
                                mime="application/pdf",
                                use_container_width=True,
                            )
                        else:
                            st.warning(
                                "PDF tidak tersedia. Alternatif: download HTML → buka di browser → Print → Save as PDF."
                            )

                st.divider()

                if st.button("🔄 Analisis Baru", type="secondary", use_container_width=True):
                    result_placeholder.empty()
                    status_placeholder.empty()
                    progress_placeholder.empty()
                    st.rerun()
            else:
                st.error("File laporan tidak ditemukan!")
                _update_history(row_id, "failed", error="File tidak ditemukan")

    except Exception as e:
        error_msg = str(e)
        _update_history(row_id, "failed", error=error_msg)
        status_placeholder.error(f"Gagal: {error_msg}")
        progress_placeholder.progress(0, text="Gagal")
        if st.button("🔄 Coba Lagi", type="secondary"):
            st.rerun()
