from pathlib import Path

import streamlit as st

from deep_research_team.backend import get_history_list
from deep_research_team.page_utils import render_breadcrumbs, render_sidebar
from deep_research_team.tools.db_utils import init_db
from deep_research_team.tools.export_utils import md_to_pdf

st.set_page_config(
    page_title="Riwayat - Deep Research Team",
    page_icon="\U0001f4cb",
    layout="wide",
)

render_sidebar()

init_db()

render_breadcrumbs(("app.py", "Beranda"), ("pages/3_History.py", "Riwayat"))
st.title("Riwayat Analisis")

search_query = st.text_input(
    "Cari analisis",
    placeholder="Filter berdasarkan bidang bisnis...",
    label_visibility="collapsed",
)
st.caption("Kosongkan untuk menampilkan semua")

offset = st.session_state.get("_history_offset", 0)
page_size = 20

items = [h.to_dict() for h in get_history_list(limit=page_size, offset=offset, search=search_query or None)]

if not items:
    st.markdown(
        '<p style="opacity: 0.6;">Belum ada analisis yang tersimpan.</p>',
        unsafe_allow_html=True,
    )
    if st.button("Ke Halaman Utama", type="primary", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

for item in items:
    with st.container():
        status = item["status"]
        status_icons = {"completed": "\u2705 Selesai", "running": "\u23f3 Berjalan", "failed": "\u274c Gagal"}
        status_label = status_icons.get(status, status)

        cols = st.columns([2, 2, 1, 1, 1])

        with cols[0]:
            st.markdown(f"**{item['field']}**")

        with cols[1]:
            st.markdown(
                f'<span style="font-size: 0.85rem; opacity: 0.6;">'
                f'{item["created_at"][:16]}</span>',
                unsafe_allow_html=True,
            )

        with cols[2]:
            st.markdown(f"`{status_label}`")

        with cols[3]:
            if st.button(
                "Lihat",
                key=f"view_{item['id']}",
                use_container_width=True,
            ):
                st.session_state.row_id = item["id"]
                st.session_state.field_clean = item["field"]
                st.switch_page("pages/1_Report.py")

        with cols[4]:
            if status == "completed":
                rp = item.get("report_path")
                report_file = Path(rp) if rp and Path(rp).exists() else None
                if report_file:
                    with open(report_file, "r", encoding="utf-8") as f:
                        md_content = f.read()

                    dcols = st.columns(2)
                    with dcols[0]:
                        st.download_button(
                            "MD",
                            data=md_content,
                            file_name=report_file.name,
                            mime="text/markdown",
                            key=f"dl_md_{item['id']}",
                            use_container_width=True,
                        )
                    with dcols[1]:
                        pdf_bytes = md_to_pdf(md_content)
                        if pdf_bytes:
                            st.download_button(
                                "PDF",
                                data=pdf_bytes,
                                file_name=report_file.with_suffix(".pdf").name,
                                mime="application/pdf",
                                key=f"dl_pdf_{item['id']}",
                                use_container_width=True,
                            )
                        else:
                            st.markdown(
                                '<span style="opacity: 0.3; font-size: 0.8rem;">-</span>',
                                unsafe_allow_html=True,
                            )
                else:
                    st.markdown(
                        '<span style="opacity: 0.3; font-size: 0.8rem;">File tidak ada</span>',
                        unsafe_allow_html=True,
                    )
            elif status == "failed":
                if st.button("Ulangi", key=f"retry_{item['id']}", use_container_width=True):
                    st.session_state.field_clean = item["field"]
                    if "row_id" in st.session_state:
                        del st.session_state.row_id
                    st.switch_page("app.py")
            elif status == "running":
                st.markdown(
                    '<span style="opacity: 0.6; font-size: 0.8rem;">⏳ progress...</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<span style="opacity: 0.3;">-</span>',
                    unsafe_allow_html=True,
                )

        st.divider()

if len(items) == page_size:
    if st.button("Muat Lagi", use_container_width=True):
        st.session_state._history_offset = offset + page_size
        st.rerun()

if offset > 0:
    col_a, col_b = st.columns([1, 3])
    with col_a:
        if st.button("← Sebelumnya", use_container_width=True):
            st.session_state._history_offset = max(0, offset - page_size)
            st.rerun()
