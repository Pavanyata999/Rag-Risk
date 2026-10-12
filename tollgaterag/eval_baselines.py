"""
Comprehensive Comparative Evaluation of SOTA Defenses across Tollgate-Bench.
Evaluates defenses strictly on RAW DOCUMENT TEXT on the topic-disjoint held-out test split.

Baselines:
1. Plain RAG (Unprotected)
2. Strict Whitelisting (Zero Trust)
3. Keyword / BIPIA Filter (Raw regex on injection markers)
4. Character-Entropy Filter (Shannon character distribution)
5. Keyword Guardrail (Simulated Content Moderation)
6. Real Model Guardrail: meta-llama/llama-prompt-guard-2-86m (Groq API, disk-cached)
7. TF-IDF + Relaxation Cues (LLM-Free heuristic anchor comparison)
8. Trust-Weighted Retrieval (Reranking by source trust weight)
9. TollgateRAG (Full Multi-Dimensional NLI Gate - Noisy-OR)
"""

import os
import json
import numpy as np
from typing import Dict, List, Tuple
from tollgaterag import config
from tollgaterag.pipeline import run_query
from tollgaterag.retriever import Retriever
from tollgaterag.eval import load_labels, load_queries, load_splits, wilson_ci
from tollgaterag.baselines import (
    baseline_unprotected,
    baseline_whitelist,
    baseline_keyword_filter,
    baseline_perplexity_filter,
    baseline_keyword_guard_simulated,
    baseline_prompt_guard_real,
    baseline_tfidf_cue
)


def compute_raw_doc_metrics(per_query: List[dict], policy_fn, k: int = 3) -> dict:
    """
    Evaluate a defense policy operating directly on raw document dictionaries:
    policy_fn(doc) -> (risk_score: float, decision: "accept" | "warn" | "reject")
    """
    stats = {
        "adversarial": {"events": 0, "rejected": 0, "warned": 0, "flagged": 0},
        "benign": {"events": 0, "rejected": 0, "warned": 0, "flagged": 0},
        "benign_hard": {"events": 0, "rejected": 0, "warned": 0, "flagged": 0},
        "low_quality": {"events": 0, "rejected": 0, "warned": 0, "flagged": 0},
        "verified": {"events": 0, "rejected": 0, "warned": 0, "flagged": 0},
    }

    q_contaminations = []
    adv_ctx_total = 0

    for item in per_query:
        scored = []
        for d in item["docs"]:
            risk, dec = policy_fn(d)
            scored.append({**d, "risk": risk, "dec": dec})

            lbl = d["label"]
            if lbl in stats:
                stats[lbl]["events"] += 1
                stats[lbl]["rejected"] += (dec == "reject")
                stats[lbl]["warned"] += (dec == "warn")
                stats[lbl]["flagged"] += (dec in ("reject", "warn"))

        # Action gate selection: admit non-rejected candidates, sorted by distance, up to k
        admitted = [d for d in scored if d["dec"] != "reject"]
        admitted.sort(key=lambda d: d.get("distance", 0.0))
        final_context = admitted[:k]

        adv_in_ctx = sum(1 for d in final_context if d["label"] == "adversarial")
        adv_ctx_total += adv_in_ctx
        q_contaminations.append(1 if adv_in_ctx > 0 else 0)

    # Compute rates and CIs
    adv = stats["adversarial"]
    adv_e = max(adv["events"], 1)
    ben = stats["benign"]
    ben_e = max(ben["events"], 1)
    ben_hard = stats["benign_hard"]
    ben_hard_e = max(ben_hard["events"], 1)

    n_q = max(len(q_contaminations), 1)
    contam_rate = sum(q_contaminations) / n_q

    return {
        "adv_reject_rate": adv["rejected"] / adv_e,
        "adv_reject_ci": list(wilson_ci(adv["rejected"], adv["events"])),
        "adv_flag_rate": adv["flagged"] / adv_e,
        "adv_flag_ci": list(wilson_ci(adv["flagged"], adv["events"])),
        "benign_reject_rate": ben["rejected"] / ben_e,
        "benign_reject_ci": list(wilson_ci(ben["rejected"], ben["events"])),
        "benign_warn_rate": ben["warned"] / ben_e,
        "benign_hard_reject_rate": ben_hard["rejected"] / ben_hard_e,
        "benign_hard_reject_ci": list(wilson_ci(ben_hard["rejected"], ben_hard["events"])),
        "benign_hard_warn_rate": ben_hard["warned"] / ben_hard_e,
        "contamination": contam_rate,
        "contamination_ci": list(wilson_ci(sum(q_contaminations), len(q_contaminations))),
        "adv_docs_in_context": adv_ctx_total,
        "events_breakdown": stats
    }


def evaluate_all_sota_baselines(split: str = "test"):
    config.set_seed()
    labels = load_labels()
    retriever = Retriever()
    anchors = retriever.verified_anchors()

    splits = load_splits()
    if split == "test":
        test_queries = load_queries(split="test")
        test_doc_ids = set(splits.get("test", {}).get("documents", []))
        print(f"Running SOTA Baselines on HELD-OUT TEST SPLIT ({len(test_queries)} queries)...")
    else:
        test_queries = load_queries(split="full")
        test_doc_ids = None
        print(f"Running SOTA Baselines on FULL CORPUS ({len(test_queries)} queries)...")

    # Collect retrieved documents per query using vector retriever
    per_query = []
    print("Collecting retrieved candidate documents for each query...")
    for q in test_queries:
        q_text = q["query"] if isinstance(q, dict) else q
        res = run_query(q_text, log=False)
        docs = []
        for r, c in zip(res["reports"], res["candidates"]):
            doc_id = r.doc_id
            if test_doc_ids and doc_id not in test_doc_ids:
                continue
            docs.append({
                "doc_id": doc_id,
                "label": labels.get(doc_id, "unknown"),
                "body": c["body"],
                "trust_level": c.get("trust_level", "unknown"),
                "date": c.get("date", "2026-09-01"),
                "distance": c.get("distance", 0.0),
                "risk_report": r
            })
        per_query.append({"query": q, "docs": docs})

    # Raw-text evaluation functions
    def eval_unprotected(doc):
        return baseline_unprotected(doc)

    def eval_whitelist(doc):
        return baseline_whitelist(doc)

    def eval_keyword(doc):
        return baseline_keyword_filter(doc)

    def eval_perplexity(doc):
        return baseline_perplexity_filter(doc)

    def eval_keyword_guard_sim(doc):
        return baseline_keyword_guard_simulated(doc)

    def eval_prompt_guard_real(doc):
        return baseline_prompt_guard_real(doc)

    def eval_tfidf_cue(doc):
        return baseline_tfidf_cue(doc, anchors)

    def eval_tollgaterag(doc):
        r = doc["risk_report"]
        return r.overall_risk, r.decision

    policy_fns = {
        "1. Plain RAG (Unprotected)": eval_unprotected,
        "2. Strict Whitelist (Zero Trust)": eval_whitelist,
        "3. Keyword / BIPIA Filter": eval_keyword,
        "4. Perplexity Filter (Anomaly)": eval_perplexity,
        "5. Keyword Guardrail (Simulated)": eval_keyword_guard_sim,
        "6. Prompt Guard Real (Meta AI 86M)": eval_prompt_guard_real,
        "7. TF-IDF + Relaxation Cues (LLM-Free)": eval_tfidf_cue,
        "8. TollgateRAG (Noisy-OR NLI Gate)": eval_tollgaterag,
    }

    results = {}
    for name, fn in policy_fns.items():
        print(f"Evaluating {name}...")
        results[name] = compute_raw_doc_metrics(per_query, fn)

    # Evaluate Trust-Weighted Retrieval separately: reranks candidate pool by trust before admitting
    print("Evaluating 9. Trust-Weighted Retrieval...")
    def eval_trust_weighted_pool(per_q):
        # Constructs modified per_query where unverified candidates are penalized in distance
        twr_queries = []
        for item in per_q:
            twr_docs = []
            for d in item["docs"]:
                # Verified sources receive a distance discount (-0.4), unverified do not
                eff_dist = d.get("distance", 0.0) - (0.4 if d.get("trust_level") == "verified" else 0.0)
                twr_docs.append({**d, "distance": eff_dist})
            twr_queries.append({"query": item["query"], "docs": twr_docs})
        # Plain pass over trust-reweighted distances
        return compute_raw_doc_metrics(twr_queries, eval_unprotected)

    results["9. Trust-Weighted Retrieval"] = eval_trust_weighted_pool(per_query)

    print("=" * 125)
    print(f"SOTA DEFENSE BENCHMARK COMPARISON ({len(test_queries)} Queries, Topic-Disjoint Split: {split})")
    print("=" * 125)
    header = f"{'Defense Mechanism':42}{'Adv Reject':>12}{'Adv Flag':>11}{'Benign FP':>12}{'Benign-Hard':>14}{'Contam.':>11}"
    print(header)
    print("-" * len(header))
    for name, m in results.items():
        print(f"{name:42}{m['adv_reject_rate']*100:>11.1f}%{m['adv_flag_rate']*100:>10.1f}%{m['benign_reject_rate']*100:>11.1f}%{m['benign_hard_reject_rate']*100:>13.1f}%{m['contamination']*100:>10.1f}%")

    out_file = os.path.join(config.LOG_DIR, "sota_baselines_comparison.json")
    clean_results = {
        "metadata": {
            "split": split,
            "query_count": len(test_queries),
            "guard_model": "meta-llama/llama-prompt-guard-2-86m via Groq API (disk-cached)",
            "config": config.get_config_dict()
        },
        "results": {k: {m_k: m_v for m_k, m_v in v.items() if m_k != "per_doc"} for k, v in results.items()}
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(clean_results, f, indent=2)
    print(f"\nSaved SOTA comparison to: {out_file}")
    return results


if __name__ == "__main__":
    evaluate_all_sota_baselines("test")
