import os
from typing import Optional

from google import genai
from google.genai import errors as genai_errors

from deep_research_team.settings import setup_logging

logger = setup_logging(__name__)

IMAGE_MODEL = "gemini-2.5-flash-preview-image"

STYLE_PROMPTS = {
    "modern minimalis": (
        "Gaya modern minimalis dengan garis bersih, ruang negatif yang lapang, "
        "dan tipografi sans-serif yang elegan."
    ),
    "klasik elegan": (
        "Gaya klasik elegan dengan ornament halus, tipografi serif, "
        "dan palet warna yang sophisticated."
    ),
    "playful kreatif": (
        "Gaya playful dan kreatif dengan warna cerah, bentuk organik, "
        "dan elemen visual yang dinamis."
    ),
    "teknologi futuristik": (
        "Gaya teknologi futuristik dengan elemen geometris, gradien digital, "
        "dan kesan inovatif."
    ),
    "natural organik": (
        "Gaya natural dan organik dengan warna earth tone, bentuk melengkung, "
        "dan elemen yang terinspirasi alam."
    ),
}

DEFAULT_STYLE = "modern minimalis"


def generate_logo_image(
    brand_name: str,
    concept: Optional[dict] = None,
    style: str = DEFAULT_STYLE,
) -> tuple[Optional[bytes], Optional[str]]:
    """Returns (image_bytes, error_message). On success error_message is None, on failure image_bytes is None."""
    if concept is None:
        concept = {}
    style_desc = STYLE_PROMPTS.get(style, STYLE_PROMPTS[DEFAULT_STYLE])
    prompt = _build_prompt(brand_name, concept, style_desc)
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        msg = "GEMINI_API_KEY tidak ditemukan di environment. Set di file .env"
        logger.error(msg)
        return None, msg
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
            config={"response_modalities": ["IMAGE", "TEXT"]},
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                return part.inline_data.data, None
        logger.warning("Response tidak mengandung image data")
        return None, "Model tidak mengembalikan data gambar. Coba gaya lain."
    except genai_errors.ClientError as exc:
        code = getattr(exc, "status_code", 0)
        if code == 429:
            msg = (
                "Kuota Gemini API habis (429). Model ini mungkin perlu billing. "
                "Aktifkan billing di Google AI Studio, atau gunakan 'Generate SVG'."
            )
        elif code == 403:
            msg = "API Key tidak valid atau tidak memiliki akses ke model ini. Periksa GEMINI_API_KEY di .env."
        elif code == 400:
            msg = f"Request tidak valid: {exc}"
        else:
            msg = f"Gemini API error ({code}): {exc}"
        logger.error(msg)
        return None, msg
    except Exception as exc:
        msg = f"Gagal generate logo: {exc}"
        logger.error(msg)
        return None, msg


def _build_prompt(brand_name: str, concept: dict, style_desc: str) -> str:
    lines = [f"Buat logo profesional untuk brand '{brand_name}'."]
    if concept.get("meaning"):
        lines.append(f"Makna nama: {concept['meaning']}")
    if concept.get("philosophy"):
        lines.append(f"Filosofi: {concept['philosophy']}")
    if concept.get("target_market"):
        lines.append(f"Target pasar: {concept['target_market']}")
    if concept.get("positioning"):
        lines.append(f"Positioning: {concept['positioning']}")
    lines.append(f"\n{style_desc}")
    lines.append(
        "\nFormat: logo dalam bentuk PNG dengan background transparan, "
        "mengandung elemen ikon dan teks brand, "
        "resolusi 1024x1024, siap pakai untuk website dan media sosial."
    )
    return "\n".join(lines)
