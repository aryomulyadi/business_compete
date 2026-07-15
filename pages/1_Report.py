import os

import streamlit as st

from deep_research_team.settings import REPORT_FILE
from deep_research_team.tools.db_utils import get_history_row
from deep_research_team.tools.export_utils import md_to_html, md_to_pdf

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

st.set_page_config(
    page_title="Laporan - Deep Research Team",
    page_icon="\U0001f4c4",
    layout="wide",
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
.stButton > button {font-weight: 600;}
</style>
"""

st.markdown(_CSS, unsafe_allow_html=True)

row_id = st.session_state.get("row_id")
field_clean = st.session_state.get("field_clean", "")

if not row_id:
    st.title("Belum Ada Laporan")
    st.markdown(
        '<p style="opacity: 0.6;">Jalankan analisis terlebih dahulu dari halaman utama.</p>',
        unsafe_allow_html=True,
    )
    if st.button("Ke Halaman Utama", type="primary", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

row = get_history_row(row_id)

if row is None:
    st.title("Laporan Tidak Ditemukan")
    st.markdown(
        '<p style="opacity: 0.6;">Data analisis tidak ditemukan di database.</p>',
        unsafe_allow_html=True,
    )
    if st.button("Ke Halaman Utama", type="primary", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

status = row["status"]
field_clean = field_clean or row["field"]

st.title("Laporan Analisis")

if field_clean:
    st.markdown(
        f'<p style="margin-top: -0.5rem; opacity: 0.6; font-size: 0.95rem;">'
        f"Bidang: {field_clean}</p>",
        unsafe_allow_html=True,
    )

if status == "failed":
    error_msg = row.get("error") or "Terjadi kesalahan yang tidak diketahui."
    st.error(f"Analisis gagal: {error_msg}")
    st.markdown(
        '<p style="opacity: 0.6;">'
        "Periksa koneksi API, saldo akun, atau coba ulangi dengan provider lain.</p>",
        unsafe_allow_html=True,
    )
    if st.button("Coba Lagi", type="primary", use_container_width=True):
        for key in ("row_id", "field_clean"):
            st.session_state.pop(key, None)
        st.switch_page("app.py")
    st.stop()

elif status == "running":
    st.warning("Analisis masih berjalan. Silakan tunggu atau cek progress di halaman utama.")
    if st.button("Ke Halaman Utama", type="primary", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

elif status != "completed":
    st.warning(f"Status analisis: {status}. Belum ada laporan untuk ditampilkan.")
    if st.button("Ke Halaman Utama", type="primary", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

if not REPORT_FILE.exists():
    st.error("File laporan tidak ditemukan di disk.")
    if st.button("Ke Halaman Utama", type="primary", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

with open(REPORT_FILE, "r", encoding="utf-8") as f:
    report_content = f.read()

html_content = md_to_html(report_content)
pdf_bytes = md_to_pdf(report_content)

tab_preview, tab_download = st.tabs(["Preview", "Download"])

with tab_preview:
    st.markdown(report_content)

with tab_download:
    dcols = st.columns(3)
    with dcols[0]:
        st.download_button(
            "Download Markdown",
            data=report_content,
            file_name=REPORT_FILE.name,
            mime="text/markdown",
            use_container_width=True,
        )
    with dcols[1]:
        st.download_button(
            "Download HTML",
            data=html_content,
            file_name=REPORT_FILE.with_suffix(".html").name,
            mime="text/html",
            use_container_width=True,
        )
    with dcols[2]:
        if pdf_bytes:
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=REPORT_FILE.with_suffix(".pdf").name,
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.warning(
                "PDF tidak tersedia. Alternatif: download HTML, buka di browser, "
                "Print > Save as PDF."
            )

st.divider()

if st.button("Analisis Baru", type="secondary", use_container_width=True):
    for key in ("row_id", "field_clean"):
        st.session_state.pop(key, None)
    st.switch_page("app.py")
