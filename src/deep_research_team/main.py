#!/usr/bin/env python
import os
import sys
import io
import warnings

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("LITELLM_DROP_PARAMS", "true")

from dotenv import load_dotenv
from deep_research_team.crew import DeepResearchCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")


def run():
    business_field = input(
        "Masukkan bidang bisnis yang ingin dianalisis (contoh: 'E-commerce Fesyen'): "
    )

    result = DeepResearchCrew().crew().kickoff(inputs={"business_field": business_field})

    print("\n" + "=" * 60)
    print("LAPORAN TELAH BERHASIL DIBUAT!")
    print("=" * 60)
    print("File: output/laporan_analisis_kompetitor.md")
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
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    try:
        DeepResearchCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    business_field = input(
        "Masukkan bidang bisnis yang ingin dianalisis (contoh: 'E-commerce Fesyen'): "
    )
    inputs = {"business_field": business_field}
    try:
        DeepResearchCrew().crew().test(
            n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    run()
