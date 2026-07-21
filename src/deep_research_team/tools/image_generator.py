import base64
import os
from typing import Optional

import requests
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

CLOUDFLARE_URL_KEY = "CLOUDFLARE_AI_URL"
CLOUDFLARE_KEY_KEY = "CLOUDFLARE_AI_KEY"
MAX_IMAGE_SIZE = 5 * 1024 * 1024


def generate_logo_image(
    brand_name: str,
    concept: Optional[dict] = None,
    style: str = DEFAULT_STYLE,
) -> tuple[Optional[bytes], Optional[str]]:
    if concept is None:
        concept = {}
    style_desc = STYLE_PROMPTS.get(style, STYLE_PROMPTS[DEFAULT_STYLE])
    prompt = _build_prompt(brand_name, concept, style_desc)

    cf_url = os.getenv(CLOUDFLARE_URL_KEY)
    cf_key = os.getenv(CLOUDFLARE_KEY_KEY)
    if cf_url and cf_key:
        result = _try_cloudflare(prompt, cf_url, cf_key)
        if result:
            err = _validate_image_bytes(result)
            if not err:
                logger.info("Logo generated via Cloudflare AI (Flux Schnell)")
                return result, None
            logger.warning("Cloudflare image too large (%s), trying Gemini", err)

    result = _try_gemini(prompt)
    if result:
        err = _validate_image_bytes(result)
        if not err:
            logger.info("Logo generated via Gemini (fallback)")
            return result, None
        logger.warning("Gemini image too large (%s)", err)

    return None, "Semua provider AI gagal. Gunakan Generate SVG."


def _try_cloudflare(prompt: str, url: str, key: str) -> Optional[bytes]:
    try:
        res = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={"prompt": prompt},
            timeout=30,
        )
        if res.status_code != 200:
            logger.warning("Cloudflare AI HTTP %s: %s", res.status_code, res.text[:200])
            return None
        data = res.json()
        if "image" not in data:
            logger.warning("Cloudflare AI response missing 'image' field")
            return None
        return base64.b64decode(data["image"])
    except requests.RequestException as exc:
        logger.warning("Cloudflare AI request failed: %s", exc)
        return None
    except (ValueError, KeyError, TypeError) as exc:
        logger.warning("Cloudflare AI parse error: %s", exc)
        return None


def _try_gemini(prompt: str) -> Optional[bytes]:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
            config={"response_modalities": ["IMAGE", "TEXT"]},
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                return part.inline_data.data
        logger.warning("Gemini response tidak mengandung image data")
        return None
    except genai_errors.ClientError as exc:
        code = getattr(exc, "status_code", 0)
        if code == 429:
            logger.warning("Gemini quota habis (429)")
        elif code == 403:
            logger.warning("Gemini API Key invalid (403)")
        else:
            logger.warning("Gemini API error (%s): %s", code, exc)
        return None
    except Exception as exc:
        logger.warning("Gemini generate error: %s", exc)
        return None


def _validate_image_bytes(data: bytes) -> Optional[str]:
    if len(data) > MAX_IMAGE_SIZE:
        return f"Image terlalu besar ({len(data) / 1024 / 1024:.1f}MB, max 5MB)"
    return None


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
