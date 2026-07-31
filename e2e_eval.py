"""E2E Evaluation: Run 3 executions and compare results."""
import json
import os
import re
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LITELLM_DROP_PARAMS"] = "true"
os.environ["LITELLM_LOG"] = "ERROR"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["CREWAI_DESERIALIZE_CALLBACKS"] = "true"
os.environ["LLM_PROVIDER"] = "groq"
os.environ.pop("OPENAI_API_KEY", None)

_env_file = Path(__file__).parent / ".env.local"
if _env_file.exists():
    for _line in _env_file.read_text("utf-8").splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _key, _val = _line.split("=", 1)
        _key, _val = _key.strip(), _val.strip().strip("\"'")
        if _val and not os.environ.get(_key):
            os.environ[_key] = _val

sys.path.insert(0, str(Path(__file__).parent))

from deep_research_team.tools.db_utils import get_history_row, save_history
from deep_research_team.tools.llm_utils import clear_llm_cache
from deep_research_team.tools.search_tool import clear_session_cache
from deep_research_team.tools.storage import read_text
from fastapi_backend.workers.crew_runner import run_crew_task
from fastapi_backend.workers.progress_store import create_task

BUSINESS_FIELD = "E-commerce Skincare Lokal"
NUM_RUNS = 3
RUN_TIMEOUT = 1200
EVAL_DIR = Path("output/eval")
EVAL_DIR.mkdir(parents=True, exist_ok=True)


def fetch_report(report_path: str) -> str:
    if report_path and report_path.startswith(("https://", "http://")):
        return read_text(report_path)
    p = Path(report_path)
    if p.exists():
        return p.read_text("utf-8")
    raise FileNotFoundError(f"Report not found: {report_path}")


def extract_competitors(text: str) -> list[str]:
    start = text.find("## 3. Profil Kompetitor Utama")
    if start < 0:
        start = text.find("## 3.")
    if start < 0:
        return []
    end = text.find("\n## ", start + 1)
    section = text[start:end] if end > start else text[start:]
    names: list[str] = []
    for m in re.finditer(r'\*{2}([A-Z][A-Za-z]+(?:[\s-][A-Z][A-Za-z]+)*):?\*{2}\s', section):
        name = m.group(1).strip()
        if len(name) >= 3 and name.lower() not in ("yang", "dengan", "untuk", "dari"):
            names.append(name)
    return names


def extract_brand_names(text: str) -> list[str]:
    start = text.find("## 8. Brand Strategy")
    if start < 0:
        start = text.find("## 8.")
    if start < 0:
        return []
    end = text.find("\n## ", start + 1)
    section = text[start:end] if end > start else text[start:]
    names: list[str] = []
    for m in re.finditer(r'\d+\.\s+\*{0,2}([A-Z][A-Za-z]+(?:[\s-][A-Z][A-Za-z]+)*)\*{0,2}:', section):
        name = m.group(1).strip()
        if len(name) >= 3 and name not in names:
            names.append(name)
    return names[:10]


def extract_executive_summary(text: str) -> str:
    start = text.find("## 1. Ringkasan Eksekutif")
    if start < 0:
        start = text.find("## 1.")
    if start < 0:
        return ""
    end = text.find("\n## ", start + 1)
    return text[start:end] if end > start else text[start:]


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


results: list[dict] = []

clear_session_cache()
clear_llm_cache()

for run in range(1, NUM_RUNS + 1):
    print(f"\n{'='*60}")
    print(f"  RUN {run}/{NUM_RUNS}: {BUSINESS_FIELD}")
    print(f"{'='*60}")

    task_id = str(uuid.uuid4())
    row_id = save_history(BUSINESS_FIELD, "pending")
    create_task(task_id, BUSINESS_FIELD, row_id)
    print(f"  Created: task_id={task_id}, row_id={row_id}")

    start_time = time.time()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(run_crew_task, task_id, BUSINESS_FIELD, row_id)
            fut.result(timeout=RUN_TIMEOUT)
    except TimeoutError:
        elapsed = time.time() - start_time
        print(f"  TIMEOUT after {elapsed:.0f}s (>{RUN_TIMEOUT}s)")
        results.append({"run": run, "status": "timeout", "elapsed": elapsed})
        continue
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ERROR at {elapsed:.0f}s: {e}")
        results.append({"run": run, "status": "failed", "error": str(e), "elapsed": elapsed})
        continue

    elapsed = time.time() - start_time
    print(f"  Completed in {elapsed:.0f}s")

    row = get_history_row(row_id)
    if not row or row["status"] != "completed":
        print(f"  WARNING: status is {row['status'] if row else 'None'}")
        results.append({"run": run, "status": row["status"] if row else "unknown", "elapsed": elapsed})
        continue

    report_path = row["report_path"]
    try:
        content = fetch_report(report_path)
    except Exception as e:
        print(f"  Error fetching report: {e}")
        results.append({"run": run, "status": "no_report", "error": str(e), "elapsed": elapsed})
        continue

    dest = EVAL_DIR / f"run_{run}.md"
    dest.write_text(content, encoding="utf-8")
    print(f"  Saved to {dest} ({len(content)} chars)")

    results.append({
        "run": run, "status": "completed", "elapsed": elapsed,
        "row_id": row_id, "report_path": report_path, "length": len(content),
    })

print(f"\n{'='*60}")
print("  SUMMARY")
print(f"{'='*60}")
for r in results:
    tag = r["status"]
    if "elapsed" in r:
        print(f"  Run {r['run']}: {tag} ({r['elapsed']:.0f}s)")
    else:
        print(f"  Run {r['run']}: {tag}")

completed = [r for r in results if r["status"] == "completed"]
if len(completed) >= 2:
    print(f"\n{'='*60}")
    print("  CONSISTENCY ANALYSIS")
    print(f"{'='*60}")

    reports: dict[int, str] = {}
    for r in completed:
        path = EVAL_DIR / f"run_{r['run']}.md"
        reports[r["run"]] = path.read_text("utf-8")

    comparison_lines: list[str] = [
        "# Consistency Report\n",
        f"Business Field: {BUSINESS_FIELD}\n",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"Total Runs: {NUM_RUNS}, Completed: {len(completed)}\n",
        "\n---\n",
    ]

    run_ids = sorted(reports.keys())
    for i, ri in enumerate(run_ids):
        for rj in run_ids[i + 1:]:
            ti = reports[ri]
            tj = reports[rj]

            comp_i = set(extract_competitors(ti))
            comp_j = set(extract_competitors(tj))
            jaccard_comp = jaccard_similarity(comp_i, comp_j)

            brand_i = set(extract_brand_names(ti))
            brand_j = set(extract_brand_names(tj))
            jaccard_brand = jaccard_similarity(brand_i, brand_j)

            summary_i = extract_executive_summary(ti)
            summary_j = extract_executive_summary(tj)

            line = (
                f"### Run {ri} vs Run {rj}\n"
                f"- **Competitor Jaccard**: {jaccard_comp:.3f}\n"
                f"  - Run {ri}: {sorted(comp_i)}\n"
                f"  - Run {rj}: {sorted(comp_j)}\n"
                f"- **Brand Name Jaccard**: {jaccard_brand:.3f}\n"
                f"  - Run {ri}: {sorted(brand_i)}\n"
                f"  - Run {rj}: {sorted(brand_j)}\n"
                f"- **Summary length**: Run {ri}={len(summary_i)} chars, "
                f"Run {rj}={len(summary_j)} chars\n"
                f"- **Report length**: Run {ri}={results[ri - 1]['length']} chars, "
                f"Run {rj}={results[rj - 1]['length']} chars\n"
            )
            comparison_lines.append(line)

            print(f"\n  Run {ri} vs Run {rj}:")
            print(f"    Competitor Jaccard: {jaccard_comp:.3f}")
            print(f"    Brand Name Jaccard: {jaccard_brand:.3f}")
            print(f"    Competitors (R{ri}): {sorted(comp_i)}")
            print(f"    Competitors (R{rj}): {sorted(comp_j)}")
            print(f"    Brand Names (R{ri}): {sorted(brand_i)}")
            print(f"    Brand Names (R{rj}): {sorted(brand_j)}")

    comp_path = EVAL_DIR / "comparison.md"
    comp_path.write_text("\n".join(comparison_lines), encoding="utf-8")
    print(f"\n  Full comparison saved to {comp_path}")

print("\nDone!")
