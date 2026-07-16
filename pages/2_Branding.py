from pathlib import Path

import streamlit as st

from deep_research_team.backend import (
    BrandConcept,
    generate_ai_logo,
    generate_svg_logo,
    get_brand_concepts,
    get_logo_history,
    save_logo_entry,
)
from deep_research_team.page_utils import render_breadcrumbs, render_sidebar
from deep_research_team.settings import REPORT_FILE
from deep_research_team.tools.db_utils import get_history_row, init_db
from deep_research_team.tools.gemini_image import STYLE_PROMPTS

st.set_page_config(
    page_title="Branding - Deep Research Team",
    page_icon="\U0001f3a8",
    layout="wide",
)

render_sidebar()

init_db()


def _brand_to_dict(bc: BrandConcept) -> dict:
    return bc.to_dict()


row_id = st.session_state.get("row_id")
field_clean = st.session_state.get("field_clean", "")

report_path = None
if row_id:
    row = get_history_row(row_id)
    if row:
        rp = row.get("report_path")
        if rp and Path(rp).exists():
            report_path = Path(rp)

if not report_path and REPORT_FILE.exists():
    report_path = REPORT_FILE

if not report_path:
    st.title("Branding & Logo")
    st.markdown(
        '<p style="opacity: 0.6;">'
        "Jalankan analisis terlebih dahulu untuk melihat rekomendasi brand.</p>",
        unsafe_allow_html=True,
    )
    if st.button("Ke Halaman Utama", type="primary", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

with open(report_path, "r", encoding="utf-8") as f:
    report_content = f.read()

brands = [_brand_to_dict(bc) for bc in get_brand_concepts(report_content)]

render_breadcrumbs(("app.py", "Beranda"), ("pages/1_Report.py", "Laporan"), ("pages/2_Branding.py", "Branding & Logo"))
st.title("Branding & Logo")

if not brands:
    st.info("Tidak ditemukan rekomendasi brand di laporan ini.")
    st.stop()

_GRID_COLS = 2

brand_rows = [brands[i:i + _GRID_COLS] for i in range(0, len(brands), _GRID_COLS)]
for row_idx, brand_row in enumerate(brand_rows):
    cols = st.columns(_GRID_COLS)
    for col_idx, brand in enumerate(brand_row):
        i = row_idx * _GRID_COLS + col_idx
        with cols[col_idx]:
            with st.container(border=True):
                st.markdown(f"### {i+1}. {brand['name']}")

                c1, c2 = st.columns(2)
                with c1:
                    if brand.get("meaning"):
                        st.markdown(f'<div class="label">Makna</div><div class="value">{brand["meaning"]}</div>', unsafe_allow_html=True)
                    if brand.get("philosophy"):
                        st.markdown(f'<div class="label">Filosofi</div><div class="value">{brand["philosophy"]}</div>', unsafe_allow_html=True)
                with c2:
                    if brand.get("target_market"):
                        st.markdown(f'<div class="label">Target Pasar</div><div class="value">{brand["target_market"]}</div>', unsafe_allow_html=True)
                    if brand.get("positioning"):
                        st.markdown(f'<div class="label">Positioning</div><div class="value">{brand["positioning"]}</div>', unsafe_allow_html=True)

                concept = {
                    "meaning": brand.get("meaning", ""),
                    "philosophy": brand.get("philosophy", ""),
                    "target_market": brand.get("target_market", ""),
                    "positioning": brand.get("positioning", ""),
                }

                col_gen_svg, col_gen_ai = st.columns(2)
                with col_gen_svg:
                    if st.button("Generate SVG", key=f"svg_{row_id}_{i}", use_container_width=True):
                        svg = generate_svg_logo(brand["name"])
                        st.session_state[f"svg_{i}"] = svg
                        st.session_state[f"ai_{i}"] = None
                        save_logo_entry(
                            history_row_id=row_id,
                            brand_name=brand["name"],
                            concept=concept,
                            svg=svg,
                            style="svg",
                        )
                        st.rerun()

                with col_gen_ai:
                    style_key = f"style_{i}"
                    style_options = list(STYLE_PROMPTS.keys())
                    style_idx = style_options.index(st.session_state.get(style_key, style_options[0]))
                    selected_style = st.selectbox(
                        "Gaya",
                        style_options,
                        index=style_idx,
                        key=f"style_sel_{i}",
                        label_visibility="collapsed",
                    )
                    st.session_state[style_key] = selected_style
                    if st.button("Generate AI Logo", key=f"ai_{row_id}_{i}", use_container_width=True):
                        with st.spinner(f"Menghasilkan logo untuk {brand['name']}..."):
                            png_bytes, err_msg = generate_ai_logo(brand["name"], concept, selected_style)
                            if png_bytes:
                                output_dir = Path("output/logos")
                                output_dir.mkdir(parents=True, exist_ok=True)
                                png_file = output_dir / f"logo_{row_id}_{i}.png"
                                png_file.write_bytes(png_bytes)
                                st.session_state[f"ai_{i}"] = str(png_file)
                                st.session_state[f"svg_{i}"] = None
                                save_logo_entry(
                                    history_row_id=row_id,
                                    brand_name=brand["name"],
                                    concept=concept,
                                    svg="",
                                    png_path=str(png_file),
                                    style=selected_style,
                                )
                                st.rerun()
                            else:
                                st.error(err_msg or "Gagal generate logo AI (error tidak diketahui).")

                svg_content = st.session_state.get(f"svg_{i}")
                ai_path = st.session_state.get(f"ai_{i}")

                if svg_content:
                    st.markdown('<div class="logo-preview">', unsafe_allow_html=True)
                    st.markdown(svg_content, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            "Download SVG",
                            data=svg_content,
                            file_name=f"logo_{brand['name'].lower().replace(' ', '_')}.svg",
                            mime="image/svg+xml",
                            key=f"dl_svg_{row_id}_{i}",
                            use_container_width=True,
                        )
                    with col_dl2:
                        with st.expander("Source SVG"):
                            st.code(svg_content, language="xml")

                if ai_path:
                    st.markdown('<div class="logo-preview">', unsafe_allow_html=True)
                    st.image(ai_path, width=300)
                    st.markdown("</div>", unsafe_allow_html=True)
                    with open(ai_path, "rb") as f:
                        png_data = f.read()
                    st.download_button(
                        "Download PNG",
                        data=png_data,
                        file_name=f"logo_{brand['name'].lower().replace(' ', '_')}.png",
                        mime="image/png",
                        key=f"dl_png_{row_id}_{i}",
                        use_container_width=True,
                    )

                logos = [lg.to_dict() for lg in get_logo_history(row_id)]
                brand_logos = [lg for lg in logos if lg["brand_name"] == brand["name"]]
                if len(brand_logos) > 1:
                    with st.expander(f"Riwayat Logo ({len(brand_logos)-1} sebelumnya)", expanded=False):
                        for prev in brand_logos[1:]:
                            lcols = st.columns([3, 1])
                            with lcols[0]:
                                st.markdown(
                                    f'<div class="logo-history">{prev["created_at"][:16]} '
                                    f'| Gaya: {prev["style"] or "-"}</div>',
                                    unsafe_allow_html=True,
                                )
                                if prev["png_path"] and Path(prev["png_path"]).exists():
                                    st.image(prev["png_path"], width=100)
                            with lcols[1]:
                                if prev["png_path"] and Path(prev["png_path"]).exists():
                                    if st.button("Gunakan", key=f"use_{prev['id']}", use_container_width=True):
                                        st.session_state[f"ai_{i}"] = prev["png_path"]
                                        st.session_state[f"svg_{i}"] = None
                                        st.rerun()

