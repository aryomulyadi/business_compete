import os
import sys

import markdown

_UNICODE_FONT = None
_BOLD_FONT = None

_FONT_CANDIDATES: list[tuple[str, str]] = [
    # Windows (most common Unicode fonts)
    ("C:\\Windows\\Fonts\\arial.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"),
    ("C:\\Windows\\Fonts\\micross.ttf", "C:\\Windows\\Fonts\\micross.ttf"),        # Microsoft Sans Serif
    ("C:\\Windows\\Fonts\\segoeui.ttf", "C:\\Windows\\Fonts\\segoeuib.ttf"),
    ("C:\\Windows\\Fonts\\verdana.ttf", "C:\\Windows\\Fonts\\verdanab.ttf"),
    ("C:\\Windows\\Fonts\\tahoma.ttf", "C:\\Windows\\Fonts\\tahomabd.ttf"),
    ("C:\\Windows\\Fonts\\calibri.ttf", "C:\\Windows\\Fonts\\calibrib.ttf"),
    ("C:\\Windows\\Fonts\\constan.ttf", "C:\\Windows\\Fonts\\constanb.ttf"),       # Constantia
]

if sys.platform == "linux":
    _FONT_CANDIDATES = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
    ]
elif sys.platform == "darwin":
    _FONT_CANDIDATES = [
        ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
        ("/Library/Fonts/Helvetica.ttf", "/Library/Fonts/Helvetica Bold.ttf"),
        (os.path.expanduser("~/Library/Fonts/Arial.ttf"), os.path.expanduser("~/Library/Fonts/Arial Bold.ttf")),
    ]

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
    import re as _re
    # Win-1252 printable range + tab/LF/CR; strip everything else
    return _re.sub(r'[^\t\n\r\x20-\x7E\xA0-\xFF]', '', text)

for candidate, bold_candidate in _FONT_CANDIDATES:
    if os.path.exists(candidate) and os.path.exists(bold_candidate):
        _UNICODE_FONT = candidate
        _BOLD_FONT = bold_candidate if candidate.lower() != bold_candidate.lower() else None
        break


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


def md_to_pdf(md_content: str) -> bytes | None:
    cleaned = _sanitize_for_pdf(md_content)

    try:
        from fpdf import FPDF

        html = markdown.markdown(cleaned, extensions=["tables", "fenced_code"])
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
        result = pdf.output(dest="S")
        if isinstance(result, bytearray):
            return bytes(result)
        if isinstance(result, bytes):
            return result
        return result.encode("latin-1")
    except Exception as exc:
        print(f"[md_to_pdf] PDF generation failed: {exc}", file=sys.stderr)
        return None
