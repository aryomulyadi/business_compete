import os

import streamlit as st

NAV_ITEMS = [
    ("app.py", "Beranda (Analisis Baru)", "🏠"),
    ("pages/1_Report.py", "Laporan", "📄"),
    ("pages/2_Branding.py", "Branding & Logo", "🎨"),
    ("pages/3_History.py", "Riwayat", "📋"),
]

SHARED_CSS = """
<style>
#MainMenu {visibility: hidden;}
div[data-testid="stSidebarNav"] {display: none;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {padding-top: 1.5rem; padding-bottom: 0;}
h1 {font-size: 2rem !important; font-weight: 700 !important;
    letter-spacing: -0.5px !important;}
h2 {font-size: 1.3rem !important; font-weight: 600 !important;}
.stButton > button {font-weight: 600;}
.stTextInput > div > div > input {font-size: 1rem;}
div[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem; padding-bottom: 1rem;
}
div[data-testid="stVerticalBlockBorder"] {
    border-radius: 10px !important;
    padding: 1rem 1.2rem !important;
    height: 100%;
}
div[data-testid="stVerticalBlockBorder"] h3 {margin-top: 0;}
.label {opacity: 0.5; font-size: 0.8rem;}
.value {margin-bottom: 0.4rem;}
.logo-preview {display: flex; justify-content: center; padding: 0.5rem 0;}
.logo-history {opacity: 0.6; font-size: 0.8rem;}
</style>
"""


def render_sidebar() -> None:
    st.markdown(SHARED_CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### Navigasi")
        for page, label, icon in NAV_ITEMS:
            st.page_link(page, label=label, icon=icon)
        st.divider()
        st.markdown(
            '<span style="opacity: 0.4; font-size: 0.75rem;">Deep Research Team v0.1</span>',
            unsafe_allow_html=True,
        )


def render_breadcrumbs(*links: tuple[str, str]) -> None:
    parts: list[str] = []
    for i, (_, label) in enumerate(links):
        is_last = i == len(links) - 1
        if is_last:
            parts.append(f'<span style="color: rgba(128,128,128,0.75); font-size: 0.85rem; font-weight: 600;">{label}</span>')
        else:
            parts.append(f'<span style="color: rgba(128,128,128,0.4); font-size: 0.85rem;">{label}</span>')
    html = ' <span style="color: rgba(128,128,128,0.2); font-size: 0.85rem;">›</span> '.join(parts)
    st.markdown(f'<div style="margin-bottom: -0.5rem;">{html}</div>', unsafe_allow_html=True)


def render_api_status() -> None:
    checks: list[tuple[str, str, str]] = []
    serper = os.getenv("SERPER_API_KEY", "")
    checks.append(("Serper", "🔑" if serper else "⚠️", "OK" if serper else "Missing"))
    mimo = os.getenv("MIMO_API_KEY", "")
    groq = os.getenv("GROQ_API_KEY", "")
    if mimo or groq:
        checks.append(("LLM", "🔑", "OK"))
    else:
        checks.append(("LLM", "⚠️", "Missing (MIMO/GROQ)"))
    gemini = os.getenv("GEMINI_API_KEY", "")
    checks.append(("Gemini", "🔑" if gemini else "⚠️", "OK" if gemini else "AI logo disabled"))

    st.markdown("### Status API")
    for name, icon, status in checks:
        st.markdown(f'<span style="font-size: 0.8rem;">{icon} {name}: {status}</span>', unsafe_allow_html=True)
    st.divider()
