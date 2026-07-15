import os
import re
import sys
from typing import Optional

import markdown

from deep_research_team.settings import setup_logging

logger = setup_logging(__name__)

_UNICODE_FONT: Optional[str] = None
_BOLD_FONT: Optional[str] = None
_FONT_INITIALIZED: bool = False


def _init_fonts() -> None:
    global _UNICODE_FONT, _BOLD_FONT, _FONT_INITIALIZED
    if _FONT_INITIALIZED:
        return

    candidates: list[tuple[str, str]]
    if sys.platform == "linux":
        candidates = [
            ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
            ("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
        ]
    elif sys.platform == "darwin":
        candidates = [
            ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
            ("/Library/Fonts/Helvetica.ttf", "/Library/Fonts/Helvetica Bold.ttf"),
            (os.path.expanduser("~/Library/Fonts/Arial.ttf"), os.path.expanduser("~/Library/Fonts/Arial Bold.ttf")),
        ]
    else:
        candidates = [
            ("C:\\Windows\\Fonts\\arial.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"),
            ("C:\\Windows\\Fonts\\micross.ttf", "C:\\Windows\\Fonts\\micross.ttf"),
            ("C:\\Windows\\Fonts\\segoeui.ttf", "C:\\Windows\\Fonts\\segoeuib.ttf"),
            ("C:\\Windows\\Fonts\\verdana.ttf", "C:\\Windows\\Fonts\\verdanab.ttf"),
            ("C:\\Windows\\Fonts\\tahoma.ttf", "C:\\Windows\\Fonts\\tahomabd.ttf"),
            ("C:\\Windows\\Fonts\\calibri.ttf", "C:\\Windows\\Fonts\\calibrib.ttf"),
            ("C:\\Windows\\Fonts\\constan.ttf", "C:\\Windows\\Fonts\\constanb.ttf"),
        ]

    for regular, bold in candidates:
        if os.path.exists(regular) and os.path.exists(bold):
            _UNICODE_FONT = regular
            _BOLD_FONT = bold if regular.lower() != bold.lower() else None
            break

    _FONT_INITIALIZED = True


def _sanitize_for_pdf(text: str) -> str:
    """Replace smart punctuation with ASCII + keep only Windows-1252 printable."""
    _table = str.maketrans({
        '\u2014': ' -- ',   # em dash
        '\u2013': '-',      # en dash
        '\u201c': '"',      # left double quote
        '\u201d': '"',      # right double quote
        '\u2018': "'",      # left single quote
        '\u2019': "'",      # right single quote
        '\u2026': '...',    # ellipsis
        '\u2022': '*',      # bullet
        '\u00b0': '°',      # degree
        '\u00a0': ' ',      # non-breaking space
    })
    text = text.translate(_table)
    return re.sub(r'[^\t\n\r\x20-\x7E\xA0-\xFF]', '', text)

_TABLE_CELL_RE = re.compile(r'<(td|th)([^>]*)>(.*?)</\1>', re.DOTALL | re.IGNORECASE)
_STRIP_TAGS_RE = re.compile(r'</?(thead|tbody|tfoot)[^>]*>', re.IGNORECASE)


def _simplify_html_for_pdf(html: str) -> str:
    html = _STRIP_TAGS_RE.sub('', html)
    def _replace_cell(m: re.Match) -> str:
        tag, attrs, content = m.group(1), m.group(2), m.group(3)
        flat = re.sub(r'<[^>]+>', '', content)
        tag_out = 'td' if tag.lower() == 'th' else tag
        return f'<{tag_out}{attrs}>{flat}</{tag_out}>'
    return _TABLE_CELL_RE.sub(_replace_cell, html)


def md_to_html(md_content: str) -> str:
    html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: auto; padding: 20px; line-height: 1.6; }}
table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
th {{ background-color: #f0f0f0; }}
h1 {{ color: #1a1a2e; border-bottom: 3px solid #e94560; padding-bottom: 8px; }}
h2 {{ color: #16213e; border-bottom: 2px solid #e94560; padding-bottom: 5px; }}
h3 {{ color: #0f3460; }}
img {{ max-width: 100%; }}
code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
pre code {{ display: block; padding: 10px; overflow-x: auto; }}
</style></head><body>{html_body}</body></html>"""


def generate_logo_svg(brand_name: str, size: int = 200) -> str:
    """Generate SVG logo with brand initials. Zero external dependencies."""
    initials = "".join(w[0].upper() for w in brand_name.split() if w)[:3]
    if not initials:
        initials = "?"
    cx = size // 2
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#e94560"/>
      <stop offset="100%" stop-color="#16213e"/>
    </linearGradient>
  </defs>
  <rect width="{size}" height="{size}" rx="{size*0.12}" fill="url(#g)"/>
  <text x="{cx}" y="{cx + size*0.04}" text-anchor="middle" dominant-baseline="central"
        font-family="Arial, sans-serif" font-weight="bold" font-size="{size*0.4}"
        fill="white">{initials}</text>
</svg>'''
    return svg


def md_to_pdf(md_content: str) -> bytes | None:
    cleaned = _sanitize_for_pdf(md_content)

    try:
        _init_fonts()
        from fpdf import FPDF

        html = markdown.markdown(cleaned, extensions=["tables", "fenced_code"])
        html = _simplify_html_for_pdf(html)
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()

        if _UNICODE_FONT:
            try:
                pdf.add_font("CustFont", "", _UNICODE_FONT)
                if _BOLD_FONT:
                    pdf.add_font("CustFont", "B", _BOLD_FONT)
                # Register italic/bold-italic variants using same files
                # (write_html() will request "I" and "BI" for <em>/<i>/<strong><em>)
                pdf.add_font("CustFont", "I", _UNICODE_FONT)
                if _BOLD_FONT:
                    pdf.add_font("CustFont", "BI", _BOLD_FONT)
                pdf.set_font("CustFont", "", 10)
            except Exception:
                pdf.set_font("Courier", "", 10)
        else:
            pdf.set_font("Courier", "", 10)

        pdf.write_html(html)
        return bytes(pdf.output())
    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        return None
