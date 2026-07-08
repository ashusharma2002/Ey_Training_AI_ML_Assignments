# tests/load/load_test_orchestrator.py
# ============================================================
# Load Testing — Orchestrator (the real code path your app uses)
#
# WHAT THIS DOES:
#   Simulates many "users" calling orchestrator.chat() AT THE SAME TIME,
#   using threads, and measures:
#     - response time per call (min / avg / median / p95 / max)
#     - success vs failure rate
#     - real throughput (questions answered per second)
#   Results are saved as a simple, readable .txt report file.
#
# HOW TO RUN:
#   python tests/load/load_test_orchestrator.py
# ============================================================
from __future__ import annotations
import sys
import time
import statistics
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.orchestrator.orchestrator import AgentOrchestrator
from src.models.schemas import PlatformState, DocumentMetadata, DocumentType

# ── CONFIGURE THIS ──────────────────────────────────────────
SAMPLE_PDF   = ROOT / "data" / "test_profiles" / "01_young_salaried_employee" / "salary_slip.pdf"
QUESTION     = "What is the applicant's monthly income?"
NUM_USERS    = 20    # start small, increase later (5 -> 10 -> 20 -> 50)
QUESTIONS_PER_USER = 3
# ─────────────────────────────────────────────────────────────


def setup_shared_document(orchestrator: AgentOrchestrator) -> PlatformState:
    print(f"Ingesting sample document: {SAMPLE_PDF.name} ...")
    state = PlatformState()
    metadata = DocumentMetadata(
        file_name=SAMPLE_PDF.name,
        file_size_kb=SAMPLE_PDF.stat().st_size / 1024,
        document_type=DocumentType.UNKNOWN,
    )
    orchestrator.ingest_document(SAMPLE_PDF, metadata, state)
    if not state.vector_store_ready:
        raise RuntimeError("Document indexing failed — check API keys / vector store config.")
    print("Document indexed successfully. Starting load test...\n")
    return state


def simulate_one_user(orchestrator: AgentOrchestrator, state: PlatformState, user_id: int) -> list[dict]:
    results = []
    for i in range(QUESTIONS_PER_USER):
        start = time.perf_counter()
        try:
            msg = orchestrator.chat(QUESTION, state)
            elapsed = time.perf_counter() - start
            results.append({"user": user_id, "q": i, "ok": True, "seconds": elapsed})
        except Exception as exc:
            elapsed = time.perf_counter() - start
            results.append({"user": user_id, "q": i, "ok": False, "seconds": elapsed, "error": str(exc)})
    return results


def main():
    orchestrator = AgentOrchestrator()
    shared_state = setup_shared_document(orchestrator)

    all_results = []
    wall_clock_start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=NUM_USERS) as pool:
        futures = [
            pool.submit(simulate_one_user, orchestrator, shared_state, uid)
            for uid in range(NUM_USERS)
        ]
        for future in as_completed(futures):
            all_results.extend(future.result())

    wall_clock_total = time.perf_counter() - wall_clock_start

    # ── Build simple, readable report ────────────────────────
    successes = [r for r in all_results if r["ok"]]
    failures  = [r for r in all_results if not r["ok"]]
    times     = [r["seconds"] for r in successes]
    sorted_times = sorted(times)

    lines = []
    lines.append("=" * 60)
    lines.append(f"LOAD TEST RESULTS — {NUM_USERS} concurrent users x {QUESTIONS_PER_USER} questions each")
    lines.append(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append(f"Total requests:        {len(all_results)}")
    lines.append(f"Successful:            {len(successes)}")
    lines.append(f"Failed:                {len(failures)}")
    lines.append(f"Failure rate:          {100 * len(failures) / len(all_results):.1f}%" if all_results else "Failure rate:          N/A")
    lines.append(f"Total wall-clock time: {wall_clock_total:.2f}s")
    lines.append(f"Throughput:            {len(all_results) / wall_clock_total:.2f} requests/sec" if wall_clock_total else "Throughput:            N/A")
    lines.append("")
    if times:
        lines.append("Response time (successful requests only):")
        lines.append(f"  min:    {min(times):.2f}s")
        lines.append(f"  avg:    {statistics.mean(times):.2f}s")
        lines.append(f"  median: {statistics.median(times):.2f}s")
        p95_index = int(len(sorted_times) * 0.95)
        lines.append(f"  p95:    {sorted_times[min(p95_index, len(sorted_times)-1)]:.2f}s")
        lines.append(f"  max:    {max(times):.2f}s")
    if failures:
        lines.append("")
        lines.append("Sample failure reasons:")
        for f in failures[:5]:
            lines.append(f"  user {f['user']}, q{f['q']}: {f.get('error', 'unknown error')}")
    lines.append("=" * 60)

    report_text = "\n".join(lines)

    # ── Save to file (plain, readable text — not JSON) ───────
    results_dir = ROOT / "tests" / "load" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    filename = f"load_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    output_path = results_dir / filename

    with open(output_path, "w") as f:
        f.write(report_text)

    print(f"Load test complete. Results saved to: {output_path}")


if __name__ == "__main__":
    main()