"""query -> retrieve -> score -> gate -> select -> generate -> log (+ review queue)."""

import time

from tollgaterag.retriever import Retriever
from tollgaterag.risk_scorer import score_candidates
from tollgaterag.action_gate import apply_gate, select_context
from tollgaterag.llm_client import generate_answer
from tollgaterag.provenance import log_query, enqueue_for_review

_retriever = None


def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def run_query(query: str, log: bool = True) -> dict:
    start = time.perf_counter()
    retriever = get_retriever()

    t0 = time.perf_counter()
    candidates = retriever.retrieve(query)
    t_retrieval = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    anchors = retriever.verified_anchors()
    t_anchor_sel = (time.perf_counter() - t1) * 1000

    t2 = time.perf_counter()
    raw_reports = score_candidates(candidates, anchors)
    t_nli_score = (time.perf_counter() - t2) * 1000

    t3 = time.perf_counter()
    reports = apply_gate(raw_reports)
    selected = select_context(candidates, reports)
    t_gating = (time.perf_counter() - t3) * 1000

    t4 = time.perf_counter()
    answer = generate_answer(query, selected)
    t_generation = (time.perf_counter() - t4) * 1000

    latency_ms = (time.perf_counter() - start) * 1000
    timing_breakdown = {
        "retrieval_ms": round(t_retrieval, 2),
        "anchor_selection_ms": round(t_anchor_sel, 2),
        "scoring_nli_ms": round(t_nli_score, 2),
        "gating_ms": round(t_gating, 2),
        "generation_ms": round(t_generation, 2),
        "total_ms": round(latency_ms, 2),
    }

    record = None
    if log:
        record = log_query(query, reports, selected, answer, latency_ms)
        enqueue_for_review(query, reports)

    return {"query": query, "answer": answer, "candidates": candidates, "reports": reports,
            "selected_ids": [s["candidate"]["id"] for s in selected],
            "latency_ms": latency_ms, "timing_breakdown": timing_breakdown,
            "provenance_record": record}


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "What's the real travel policy, is there an unlimited allowance?"
    res = run_query(q)
    print(f"\nQUERY: {res['query']}\n")
    for r in res["reports"]:
        print(f"[{r.decision.upper():6}] risk={r.overall_risk:.2f}  {r.title} ({r.doc_id})")
        for reason in r.reasons:
            print(f"          - {reason}")
    print("\n--- ANSWER ---\n" + res["answer"])
    print(f"\n(latency: {res['latency_ms']:.1f} ms)")
