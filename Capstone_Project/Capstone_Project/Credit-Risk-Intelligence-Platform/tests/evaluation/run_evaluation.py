# tests/evaluation/run_evaluation.py
# ============================================================
# Evaluation Framework Runner — the EASIEST way to evaluate the app.
#
# What this does:
#   1. Loads test_cases.json (your fixed question set)
#   2. Asks each question to the REAL AI Chat pipeline
#   3. Scores every answer with RAGAS (faithfulness, relevancy)
#      and DeepEval (hallucination detection)
#   4. Prints a clean pass/fail report to your terminal
#   5. Saves a JSON report to tests/evaluation/results/
#
# HOW TO RUN:
#   python tests/evaluation/run_evaluation.py
#
# REQUIREMENTS:
#   - You must have already uploaded + processed documents in the
#     Streamlit app at least once (so a vector index exists)
#   - EVALUATION_ENABLED=true in .env
#   - pip install ragas deepeval datasets
# ============================================================
from __future__ import annotations
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Windows PowerShell sometimes uses a non-UTF8 codepage, which can crash
# on emoji characters (UnicodeEncodeError). Force UTF-8 output safely.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

def _find_project_root(start: Path) -> Path:
    """
    Walk upward from this file until we find the actual project root
    (identified by app.py + config/ existing together). This makes the
    script work correctly regardless of whether it's placed at
    tests/evaluation/run_evaluation.py OR <project_root>/evaluation/run_evaluation.py
    — hardcoding a fixed number of .parent calls broke when the folder
    was placed at a different depth than originally assumed.
    """
    current = start
    for _ in range(6):
        if (current / "app.py").exists() and (current / "config").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent
    # Fallback: assume tests/evaluation/run_evaluation.py layout
    return start.parent.parent.parent


ROOT = _find_project_root(Path(__file__).parent)
sys.path.insert(0, str(ROOT))

from config.settings import settings
from src.orchestrator.orchestrator import AgentOrchestrator
from src.models.schemas import PlatformState
from src.evaluation.ragas_runner import evaluate_rag_response
from src.evaluation.deepeval_runner import evaluate_hallucination

TEST_CASES_FILE = Path(__file__).parent / "test_cases.json"
RESULTS_DIR     = Path(__file__).parent / "results"


def _load_test_cases() -> list[dict]:
    if not TEST_CASES_FILE.exists():
        print(f"❌ Test cases file not found: {TEST_CASES_FILE}")
        sys.exit(1)
    data = json.loads(TEST_CASES_FILE.read_text(encoding="utf-8"))
    return data["test_cases"]


def _check_prerequisites() -> None:
    problems = []
    if not settings.GEMINI_API_KEY and not settings.OPENAI_API_KEY:
        problems.append("No GEMINI_API_KEY or OPENAI_API_KEY set in .env")
    if not settings.OPENAI_API_KEY:
        problems.append("OPENAI_API_KEY not set (required for embeddings)")

    if problems:
        print("❌ Cannot run evaluation — fix these first:\n")
        for p in problems:
            print(f"   - {p}")
        sys.exit(1)

    if not settings.EVALUATION_ENABLED:
        print(
            "⚠️  EVALUATION_ENABLED=false in .env — RAGAS/DeepEval scores will be skipped.\n"
            "    Set EVALUATION_ENABLED=true in .env to get quality scores.\n"
            "    Continuing anyway to test that Chat itself works...\n"
        )


def _print_header(text: str) -> None:
    print("\n" + "=" * 78)
    print(text)
    print("=" * 78)


def main() -> None:
    _print_header("🧪 EVALUATION FRAMEWORK — Credit Risk Intelligence Platform")
    _check_prerequisites()

    test_cases = _load_test_cases()
    print(f"\nLoaded {len(test_cases)} test cases from {TEST_CASES_FILE.name}\n")

    print("⚠️  IMPORTANT: This script needs documents already indexed.")
    print("    If you haven't uploaded documents via the Streamlit app yet,")
    print("    this will fail. Run the app, upload + process a PDF first.\n")
    input("Press ENTER to continue (or Ctrl+C to cancel)...")

    orchestrator = AgentOrchestrator()
    state        = PlatformState()

    # BUG FIX: previously checked orchestrator.vector_store_ready WITHOUT
    # ever forcing the retrieval agent to actually connect first. The
    # underlying store object is created lazily on first use — so on a
    # fresh process, _vs was still None, is_ready short-circuited to
    # False immediately, and Pinecone was never even contacted. This
    # produced a misleading "Pinecone connection failed" message even
    # when Pinecone credentials were perfectly fine.
    print(f"Connecting to vector store ({settings.VECTOR_STORE_PROVIDER})...")
    try:
        store = orchestrator._retrieval_agent._get_store()
    except Exception as exc:
        print(f"\n❌ Could not initialise vector store: {exc}\n")
        sys.exit(1)

    if settings.VECTOR_STORE_PROVIDER == "faiss":
        # FAISS needs an explicit load() call to read the persisted index
        # from disk (by design — see retrieval_agent.py comment on why
        # it doesn't auto-load on every app startup).
        loaded = store.load()
        if not loaded:
            print(
                "\n❌ No persisted FAISS index found on disk.\n"
                "   Upload + process documents via the Streamlit app first.\n"
            )
            sys.exit(1)
        print("✅ Persisted FAISS index loaded successfully.\n")
    else:
        # Pinecone is a live cloud connection — is_ready now correctly
        # checks the REAL vector count in your Pinecone index (not an
        # in-process counter), so this works even though this script is
        # a separate process from the Streamlit app that did the upload.
        if not orchestrator.vector_store_ready:
            error = orchestrator.vector_store_error or "Unknown error."
            print(
                f"\n❌ Pinecone is not ready.\n\n"
                f"Reason: {error}\n\n"
                f"Things to check:\n"
                f"  1. Did you upload + process documents via Streamlit already?\n"
                f"  2. Is PINECONE_API_KEY correct in .env?\n"
                f"  3. Does the index '{settings.PINECONE_INDEX_NAME}' exist in your Pinecone dashboard?\n"
                f"  4. Does OPENAI_EMBEDDING_DIMENSIONS in .env match your Pinecone index's dimension?\n"
            )
            sys.exit(1)
        print("✅ Pinecone connected and index has existing vectors.\n")

    results = []
    _print_header(f"Running {len(test_cases)} Test Cases")

    for i, tc in enumerate(test_cases, 1):
        tc_id      = tc["id"]
        question   = tc["question"]
        ground_truth = tc.get("expected_answer", "")
        category   = tc.get("category", "general")

        print(f"\n[{i}/{len(test_cases)}] {tc_id} ({category})")
        print(f"  Q: {question}")

        t0 = time.time()
        try:
            retrieved = orchestrator._retrieval_agent.retrieve(question)
            response  = orchestrator._chat_agent.answer_question(question, retrieved)
            answer    = response.content
            elapsed   = round(time.time() - t0, 2)

            # ── Print retrieved chunks so faithfulness is visible ──────────
            # This shows EXACTLY which document chunks the AI used to answer.
            # Faithfulness measures whether the answer stuck to these chunks.
            # If the answer contains facts NOT in these chunks = hallucination.
            if retrieved:
                print(f"  📄 Retrieved {len(retrieved)} chunk(s) used for this answer:")
                for ci, doc in enumerate(retrieved[:3], 1):
                    source = doc.metadata.get("source", "unknown")
                    page   = doc.metadata.get("page", "?")
                    # Skip boilerplate — show actual financial data
                    lines = doc.page_content.strip().split("\n")
                    skip_kw = ["fictional test", "made up", "purposes only", "[source:", "[page", "note —"]
                    useful = [l.strip() for l in lines if l.strip() and not any(k in l.lower() for k in skip_kw)]
                    preview = " | ".join(useful[:4])[:120]
                    print(f"     [{ci}] {source} (page {page}): {preview}...")
            # ──────────────────────────────────────────────────────────────

            print(f"  A: {answer[:150]}{'...' if len(answer) > 150 else ''}")
            print(f"  ⏱  {elapsed}s")
        except Exception as exc:
            print(f"  ❌ ERROR: {exc}")
            results.append({
                "id": tc_id, "question": question, "status": "ERROR",
                "error": str(exc),
            })
            continue

        # ── Save retrieved chunks into result so trainer can see them ──────
        retrieved_chunks = []
        for doc in retrieved:
            # Skip boilerplate header lines — show only actual financial data
            lines = doc.page_content.strip().split("\n")
            skip_keywords = [
                "fictional test document", "made up for software testing",
                "purposes only", "[source:", "[page", "note —"
            ]
            meaningful_lines = [
                line.strip() for line in lines
                if line.strip()
                and not any(kw in line.lower() for kw in skip_keywords)
            ]
            clean_text = " | ".join(meaningful_lines[:8])  # show first 8 meaningful lines
            retrieved_chunks.append({
                "source": doc.metadata.get("source", "unknown"),
                "page":   doc.metadata.get("page", "?"),
                "text":   clean_text[:400],
            })

        result_row = {
            "id": tc_id,
            "category": category,
            "question": question,
            "answer": answer,
            "expected_answer": ground_truth,
            "elapsed_seconds": elapsed,
            "status": "COMPLETED",
            "retrieved_chunks": retrieved_chunks,
            "chunks_count": len(retrieved_chunks),
        }

        # Negative-test check: did the AI correctly refuse to answer?
        if category == "negative_test":
            refused_correctly = any(
                phrase in answer.lower()
                for phrase in ["not available", "couldn't find", "not found", "no information"]
            )
            result_row["correctly_refused"] = refused_correctly
            print(f"  {'✅' if refused_correctly else '🔴'} Correctly refused trap question: {refused_correctly}")

        # RAGAS scoring (if enabled)
        if settings.EVALUATION_ENABLED:
            ragas_scores = evaluate_rag_response(question, answer, retrieved, ground_truth)
            if ragas_scores:
                result_row["ragas"] = ragas_scores
                faith = ragas_scores.get("faithfulness", "N/A")
                relev = ragas_scores.get("answer_relevancy", "N/A")
                print(f"  📊 RAGAS — faithfulness: {faith}, relevancy: {relev}")
                if isinstance(faith, float):
                    if faith >= 0.8:
                        print(f"     ✅ Faithfulness {faith:.2f}: AI answer closely matches the {len(retrieved)} chunks shown above")
                    elif faith >= 0.5:
                        print(f"     ⚠️  Faithfulness {faith:.2f}: AI answer partially uses chunks — some outside info added")
                    else:
                        print(f"     🔴 Faithfulness {faith:.2f}: AI answer diverges from chunks — possible hallucination")

            deepeval_scores = evaluate_hallucination(question, answer, retrieved)
            if deepeval_scores:
                result_row["deepeval"] = deepeval_scores
                grounded = "✅ GROUNDED" if deepeval_scores.get("is_grounded") else "🔴 HALLUCINATED"
                hall_score = deepeval_scores.get("hallucination_score", "N/A")
                print(f"  🧠 DeepEval — hallucination: {hall_score} ({grounded})")
                if isinstance(hall_score, float) and hall_score > 0.3:
                    print(f"     ⚠️  Score {hall_score:.2f}: Answer contains info NOT found in chunks above")

        results.append(result_row)

    _print_summary(results)
    _save_results(results)


def _print_summary(results: list[dict]) -> None:
    _print_header("📋 SUMMARY REPORT")

    completed = [r for r in results if r["status"] == "COMPLETED"]
    errored   = [r for r in results if r["status"] == "ERROR"]

    print(f"\nTotal test cases: {len(results)}")
    print(f"  ✅ Completed: {len(completed)}")
    print(f"  ❌ Errors:    {len(errored)}")

    if errored:
        print("\nErrored test cases:")
        for r in errored:
            print(f"  - {r['id']}: {r['error']}")

    # Negative test (trap question) summary
    neg_tests = [r for r in completed if r.get("category") == "negative_test"]
    if neg_tests:
        correct = sum(1 for r in neg_tests if r.get("correctly_refused"))
        print(f"\n🪤 Trap Questions (hallucination check): {correct}/{len(neg_tests)} correctly refused")

    # RAGAS averages
    ragas_results = [r["ragas"] for r in completed if "ragas" in r]
    if ragas_results:
        avg_faith = sum(r.get("faithfulness", 0) for r in ragas_results) / len(ragas_results)
        avg_rel   = sum(r.get("answer_relevancy", 0) for r in ragas_results) / len(ragas_results)
        print(f"\n📊 RAGAS Averages ({len(ragas_results)} scored):")
        print(f"  Faithfulness:     {avg_faith:.3f}  {'✅ Good' if avg_faith >= 0.7 else '⚠️ Needs review'}")
        print(f"  Answer Relevancy: {avg_rel:.3f}  {'✅ Good' if avg_rel >= 0.7 else '⚠️ Needs review'}")
    else:
        print("\n📊 RAGAS: No scores recorded (EVALUATION_ENABLED=false or ragas not installed)")

    # DeepEval averages
    deepeval_results = [r["deepeval"] for r in completed if "deepeval" in r]
    if deepeval_results:
        avg_halluc = sum(r.get("hallucination_score", 0) for r in deepeval_results) / len(deepeval_results)
        grounded_count = sum(1 for r in deepeval_results if r.get("is_grounded"))
        print(f"\n🧠 DeepEval Averages ({len(deepeval_results)} scored):")
        print(f"  Hallucination Score: {avg_halluc:.3f}  {'✅ Good (low)' if avg_halluc < 0.3 else '⚠️ Needs review'}")
        print(f"  Grounded Answers:    {grounded_count}/{len(deepeval_results)}")
    else:
        print("\n🧠 DeepEval: No scores recorded (EVALUATION_ENABLED=false or deepeval not installed)")

    avg_time = sum(r.get("elapsed_seconds", 0) for r in completed) / max(len(completed), 1)
    print(f"\n⏱  Average response time: {avg_time:.2f}s")


def _save_results(results: list[dict]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path  = RESULTS_DIR / f"eval_run_{timestamp}.json"
    out_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\n💾 Full results saved to: {out_path}")
    print(f"   (Use this file as evidence of evaluation for your capstone submission)\n")


if __name__ == "__main__":
    main()
