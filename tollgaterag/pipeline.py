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
    candidates = retriever.retrieve(query)
    reports = apply_gate(score_candidates(candidates, retriever.verified_anchors()))
    selected = select_context(candidates, reports)
    answer = generate_answer(query, selected)
    latency_ms = (time.perf_counter() - start) * 1000

    record = None
    if log:
        record = log_query(query, reports, selected, answer, latency_ms)
        enqueue_for_review(query, reports)

    return {"query": query, "answer": answer, "candidates": candidates, "reports": reports,
            "selected_ids": [s["candidate"]["id"] for s in selected],
            "latency_ms": latency_ms, "provenance_record": record}


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
