import os

import streamlit as st

from deep_research_team.settings import REPORT_FILE
from deep_research_team.tools.db_utils import get_history, init_db
from deep_research_team.tools.export_utils import md_to_pdf

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

st.set_page_config(
    page_title="Riwayat - Deep Research Team",
    page_icon="\U0001f4cb",
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

init_db()

st.title("Riwayat Analisis")

items = get_history(50)

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
            if status == "completed" and REPORT_FILE.exists():
                with open(REPORT_FILE, "r", encoding="utf-8") as f:
                    md_content = f.read()

                dcols = st.columns(2)
                with dcols[0]:
                    st.download_button(
                        "MD",
                        data=md_content,
                        file_name=REPORT_FILE.name,
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
                            file_name=REPORT_FILE.with_suffix(".pdf").name,
                            mime="application/pdf",
                            key=f"dl_pdf_{item['id']}",
                            use_container_width=True,
                        )
                    else:
                        st.markdown(
                            '<span style="opacity: 0.3; font-size: 0.8rem;">-</span>',
                            unsafe_allow_html=True,
                        )
            elif status == "failed":
                if st.button("Ulangi", key=f"retry_{item['id']}", use_container_width=True):
                    st.session_state.field_clean = item["field"]
                    if "row_id" in st.session_state:
                        del st.session_state.row_id
                    st.switch_page("app.py")
            else:
                st.markdown(
                    '<span style="opacity: 0.3;">-</span>',
                    unsafe_allow_html=True,
                )

        st.divider()
