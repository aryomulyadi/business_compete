#!/usr/bin/env python
import io
import os
import sys
import warnings

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("LITELLM_DROP_PARAMS", "true")

from dotenv import load_dotenv

from deep_research_team.crew import DeepResearchCrew
from deep_research_team.settings import (
    ENV_VARS,
    REPORT_FILE,
    setup_logging,
)
from deep_research_team.tools.export_utils import md_to_html, md_to_pdf
from deep_research_team.tools.progress import ProgressCallback, reset_progress
from deep_research_team.tools.search_tool import check_serper_api_key, filter_fake_urls_from_report

logger = setup_logging(__name__)

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()

for var in ENV_VARS:
    os.environ[var] = os.getenv(var, "")


def check_serper() -> bool:
    ok, msg = check_serper_api_key()
    if not ok:
        logger.warning("Serper API: %s", msg)
        logger.warning("Pencarian internet mungkin gagal dan LLM bisa menghasilkan data palsu.")
    else:
        logger.info("Serper API: %s", msg)
    return ok


def run():
    reset_progress()
    check_serper()

    business_field = input(
        "Masukkan bidang bisnis yang ingin dianalisis (contoh: 'E-commerce Fesyen'): "
    )
    business_field = business_field.strip()[:200]
    if not business_field:
        print("Bidang bisnis tidak boleh kosong.")
        return

    result = DeepResearchCrew().crew().kickoff(inputs={"business_field": business_field})

    ProgressCallback().finalize()

    print()
    print("=" * 60)
    print("  LAPORAN TELAH BERHASIL DIBUAT!")
    print("=" * 60)

    md_path = str(REPORT_FILE)
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        if len(md_content.strip()) < 50:
            logger.warning("Report terlalu pendek (%d chars), kemungkinan analisis gagal. Skip export.", len(md_content.strip()))
            print(f"  File report terlalu pendek — analisis mungkin gagal.")
            print(f"  Cek: {md_path}")
            print("=" * 60)
            return result

        md_content = filter_fake_urls_from_report(md_content)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        html_path = md_path.replace(".md", ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(md_to_html(md_content))

        pdf_bytes = md_to_pdf(md_content)
        pdf_path = md_path.replace(".md", ".pdf")
        if pdf_bytes:
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
            print(f"  PDF:      {pdf_path}")
        else:
            print(f"  PDF:      (tidak tersedia, buka HTML lalu print-to-PDF)")

        print(f"  Markdown: {md_path}")
        print(f"  HTML:     {html_path}")
    else:
        print(f"  File tidak ditemukan: {md_path}")
    print("=" * 60)
    return result


def train():
    business_field = input(
        "Masukkan bidang bisnis yang ingin dianalisis (contoh: 'E-commerce Fesyen'): "
    )
    inputs = {"business_field": business_field}
    try:
        DeepResearchCrew().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )
    except IndexError:
        logger.error("train: argumen tidak lengkap. Gunakan: train <n_iterations> <filename>")
        raise
    except Exception as e:
        logger.exception("Gagal menjalankan training")
        raise


def replay():
    try:
        DeepResearchCrew().crew().replay(task_id=sys.argv[1])
    except IndexError:
        logger.error("replay: argumen task_id tidak diberikan")
        raise
    except Exception as e:
        logger.exception("Gagal menjalankan replay")
        raise


def test():
    business_field = input(
        "Masukkan bidang bisnis yang ingin dianalisis (contoh: 'E-commerce Fesyen'): "
    )
    inputs = {"business_field": business_field}
    try:
        DeepResearchCrew().crew().test(
            n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs
        )
    except IndexError:
        logger.error("test: argumen tidak lengkap. Gunakan: test <n_iterations> <eval_llm>")
        raise
    except Exception as e:
        logger.exception("Gagal menjalankan test")
        raise


if __name__ == "__main__":
    run()
