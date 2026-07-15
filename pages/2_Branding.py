import os
import re

import streamlit as st

from deep_research_team.settings import REPORT_FILE
from deep_research_team.tools.export_utils import generate_logo_svg

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

st.set_page_config(
    page_title="Branding - Deep Research Team",
    page_icon="\U0001f3a8",
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
.logo-preview {display: flex; justify-content: center; padding: 1rem 0;}
</style>
"""

st.markdown(_CSS, unsafe_allow_html=True)

row_id = st.session_state.get("row_id")

if not row_id or not REPORT_FILE.exists():
    st.title("Branding & Logo")
    st.markdown(
        '<p style="opacity: 0.6;">'
        "Jalankan analisis terlebih dahulu untuk melihat rekomendasi brand.</p>",
        unsafe_allow_html=True,
    )
    if st.button("Ke Halaman Utama", type="primary", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

with open(REPORT_FILE, "r", encoding="utf-8") as f:
    report_content = f.read()

suggested_names = []
m = re.search(r'##\s*8\.\s*Brand Strategy.*?(?:$|\n##)', report_content, re.DOTALL)
if m:
    section = m.group(0)
    for line in section.split("\n"):
        line = line.strip()
        if line.startswith("- **") or line.startswith("* **"):
            name = re.sub(r'^[-*]\s*\*\*(.*?)\*\*.*', r'\1', line)
            if name and name != line:
                suggested_names.append(name)

st.title("Branding & Logo")

if suggested_names:
    with st.expander("Rekomendasi Nama Brand dari Laporan", expanded=False):
        for name in suggested_names:
            st.markdown(f"- {name}")
        st.caption("Nama-nama ini diekstrak dari seksi Brand Strategy laporan.")

st.markdown("### Buat Logo SVG")
st.markdown("Masukkan nama brand untuk menghasilkan logo berbentuk SVG.")

brand_name = st.text_input(
    "Nama Brand",
    value=suggested_names[0] if suggested_names else "",
    placeholder="Contoh: TechGrowth, FashInnovate",
    label_visibility="collapsed",
)

if brand_name:
    brand_name = brand_name.strip()
    svg = generate_logo_svg(brand_name)

    st.markdown('<div class="logo-preview">', unsafe_allow_html=True)
    st.markdown(svg, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.download_button(
        "Download SVG",
        data=svg,
        file_name=f"logo_{brand_name.lower().replace(' ', '_')}.svg",
        mime="image/svg+xml",
        use_container_width=True,
    )

    with st.expander("Lihat source SVG"):
        st.code(svg, language="xml")
