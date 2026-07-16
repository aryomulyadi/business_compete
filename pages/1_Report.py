import time
from pathlib import Path

import streamlit as st

from deep_research_team.backend import get_brand_names
from deep_research_team.page_utils import render_breadcrumbs, render_sidebar
from deep_research_team.settings import REPORT_FILE
from deep_research_team.tools.db_utils import get_history_row
from deep_research_team.tools.export_utils import md_to_html, md_to_pdf

st.set_page_config(
    page_title="Laporan - Deep Research Team",
    page_icon="\U0001f4c4",
    layout="wide",
)

render_sidebar()


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

render_breadcrumbs(("app.py", "Beranda"), ("pages/1_Report.py", "Laporan"))
st.title(f"Laporan{': ' + field_clean if field_clean else ' Analisis'}")

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
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Ke Halaman Utama (Progress)", type="primary", use_container_width=True):
            st.switch_page("app.py")
    with col_b:
        if st.button("Refresh", type="secondary", use_container_width=True):
            st.rerun()
    time.sleep(2)
    st.rerun()

elif status != "completed":
    st.warning(f"Status analisis: {status}. Belum ada laporan untuk ditampilkan.")
    if st.button("Ke Halaman Utama", type="primary", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

rp = row.get("report_path")
report_file = Path(rp) if rp and Path(rp).exists() else REPORT_FILE

if not report_file.exists():
    st.error("File laporan tidak ditemukan di disk.")
    if st.button("Ke Halaman Utama", type="primary", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

with open(report_file, "r", encoding="utf-8") as f:
    report_content = f.read()

html_content = md_to_html(report_content)
pdf_bytes = md_to_pdf(report_content)

tab_preview, tab_download, tab_branding = st.tabs(["Preview", "Download", "Branding"])

with tab_preview:
    st.markdown(report_content)
    if st.button("↑ Ke Atas", type="secondary"):
        st.markdown('<script>window.scrollTo(0,0);</script>', unsafe_allow_html=True)

with tab_download:
    dcols = st.columns(3)
    with dcols[0]:
        st.download_button(
            "Download Markdown",
            data=report_content,
            file_name=report_file.name,
            mime="text/markdown",
            use_container_width=True,
        )
    with dcols[1]:
        st.download_button(
            "Download HTML",
            data=html_content,
            file_name=report_file.with_suffix(".html").name,
            mime="text/html",
            use_container_width=True,
        )
    with dcols[2]:
        if pdf_bytes:
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=report_file.with_suffix(".pdf").name,
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.warning(
                "PDF tidak tersedia. Alternatif: download HTML, buka di browser, "
                "Print > Save as PDF."
            )

with tab_branding:
    st.markdown("### Rekomendasi Brand")
    brand_names = get_brand_names(report_content)
    if brand_names:
        for name in brand_names:
            if st.button(f"Buat Logo untuk {name}", key=f"brand_{name}", use_container_width=True):
                st.session_state.brand_name = name
                st.switch_page("pages/2_Branding.py")
    else:
        st.caption("Tidak ditemukan rekomendasi brand di laporan.")

st.divider()

if st.button("Analisis Baru", type="secondary", use_container_width=True):
    for key in ("row_id", "field_clean"):
        st.session_state.pop(key, None)
    st.switch_page("app.py")
