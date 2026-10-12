"""
Topic-Resplit Evaluation Script: scripts/evaluate_resplits.py

Evaluates TollgateRAG (Noisy-OR default) across multiple topic-disjoint splits (at least 3 different seeds).
Reports mean and range of:
- Adversarial Reject Rate (ARR)
- Benign-Hard Reject Rate (FPR)
- Context Contamination Rate

Saves full results to logs/resplit_results.json.
"""

import os
import sys
import json
import random
import numpy as np
from typing import Dict, Any, List

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
LOG_PATH = os.path.join(BASE_DIR, "logs", "resplit_results.json")

from tollgaterag import config
from tollgaterag.eval import collect, load_queries, compute_metrics, policy_tollgate


def generate_topic_disjoint_split(seed: int, all_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Partitions the 30 topics into 6 train, 12 val, 12 test topics topic-disjointly.
    """
    topics_by_domain = {}
    for q in all_queries:
        domain = q.get("domain", "default")
        topic = q.get("topic", "")
        if domain not in topics_by_domain:
            topics_by_domain[domain] = set()
        topics_by_domain[domain].add(topic)

    rng = random.Random(seed)
    train_topics = []
    val_topics = []
    test_topics = []

    # Domain-balanced topic allocation (5 topics per domain: 1 train, 2 val, 2 test)
    for domain, d_topics in sorted(topics_by_domain.items()):
        shuffled = sorted(list(d_topics))
        rng.shuffle(shuffled)
        train_topics.extend(shuffled[:1])
        val_topics.extend(shuffled[1:3])
        test_topics.extend(shuffled[3:5])

    return {
        "seed": seed,
        "train_topics": train_topics,
        "val_topics": val_topics,
        "test_topics": test_topics
    }


def main():
    print("Loading all 60 benchmark queries across all 30 topics...")
    all_queries = load_queries(split="full")
    print(f"Loaded {len(all_queries)} queries.")

    print("Running TollgateRAG inference collection on all 60 queries...")
    per_query_all, latencies = collect(all_queries, log=False)
    print(f"Collected {len(per_query_all)} evaluated query profiles.")

    # 3 independent resplit seeds + original baseline seed
    seeds = [1234, 42, 2026, 9999]
    resplit_evaluations = []

    pol_noisy_or = policy_tollgate()

    for seed in seeds:
        split_def = generate_topic_disjoint_split(seed, all_queries)
        test_topics_set = set(split_def["test_topics"])

        # Filter pre-collected query profiles to this split's test topics
        test_per_query = [q for q in per_query_all if q.get("topic") in test_topics_set]

        metrics = compute_metrics(test_per_query, pol_noisy_or)
        adv_m = metrics["adversarial_metrics"]
        bh_m = metrics["benign_hard_metrics"]
        cl_m = metrics["benign_metrics"]
        contam_m = metrics["contamination_metrics"]

        record = {
            "seed": seed,
            "test_topics_count": len(split_def["test_topics"]),
            "test_queries_count": len(test_per_query),
            "adversarial_exposures": adv_m["events"],
            "adversarial_reject_rate": round(adv_m["reject_rate"], 4),
            "adversarial_reject_ci_95": adv_m["reject_ci_95"],
            "benign_hard_exposures": bh_m["events"],
            "benign_hard_reject_rate": round(bh_m["reject_rate"], 4),
            "benign_hard_reject_ci_95": bh_m["reject_ci_95"],
            "clean_benign_exposures": cl_m["events"],
            "clean_benign_reject_rate": round(cl_m["reject_rate"], 4),
            "clean_benign_reject_ci_95": cl_m["reject_ci_95"],
            "contamination_rate": round(contam_m["contamination_rate"], 4),
            "contamination_ci_95": contam_m["contamination_ci_95"]
        }
        resplit_evaluations.append(record)
        print(f"Seed {seed}: ARR = {record['adversarial_reject_rate']*100:.1f}%, "
              f"Benign-Hard Reject = {record['benign_hard_reject_rate']*100:.1f}%, "
              f"Contamination = {record['contamination_rate']*100:.1f}%")

    # Aggregate stats across splits
    arr_vals = [r["adversarial_reject_rate"] for r in resplit_evaluations]
    bh_vals = [r["benign_hard_reject_rate"] for r in resplit_evaluations]
    contam_vals = [r["contamination_rate"] for r in resplit_evaluations]
    clean_vals = [r["clean_benign_reject_rate"] for r in resplit_evaluations]

    summary = {
        "num_splits_evaluated": len(seeds),
        "seeds": seeds,
        "adversarial_reject": {
            "mean": round(float(np.mean(arr_vals)), 4),
            "std": round(float(np.std(arr_vals)), 4),
            "min": round(float(np.min(arr_vals)), 4),
            "max": round(float(np.max(arr_vals)), 4),
            "range": [round(float(np.min(arr_vals)), 4), round(float(np.max(arr_vals)), 4)]
        },
        "benign_hard_reject": {
            "mean": round(float(np.mean(bh_vals)), 4),
            "std": round(float(np.std(bh_vals)), 4),
            "min": round(float(np.min(bh_vals)), 4),
            "max": round(float(np.max(bh_vals)), 4),
            "range": [round(float(np.min(bh_vals)), 4), round(float(np.max(bh_vals)), 4)]
        },
        "clean_benign_reject": {
            "mean": round(float(np.mean(clean_vals)), 4),
            "std": round(float(np.std(clean_vals)), 4),
            "min": round(float(np.min(clean_vals)), 4),
            "max": round(float(np.max(clean_vals)), 4),
            "range": [round(float(np.min(clean_vals)), 4), round(float(np.max(clean_vals)), 4)]
        },
        "contamination": {
            "mean": round(float(np.mean(contam_vals)), 4),
            "std": round(float(np.std(contam_vals)), 4),
            "min": round(float(np.min(contam_vals)), 4),
            "max": round(float(np.max(contam_vals)), 4),
            "range": [round(float(np.min(contam_vals)), 4), round(float(np.max(contam_vals)), 4)]
        }
    }

    final_payload = {
        "metadata": {
            "description": "Multi-seed topic-disjoint resplit sensitivity analysis",
            "model": "TollgateRAG (Noisy-OR default)",
            "date": "2026-10-12"
        },
        "summary": summary,
        "splits": resplit_evaluations
    }

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)

    print("\n============================================================")
    print("TOPIC RESPLIT SUMMARY ACROSS SEEDS")
    print(f"ARR: Mean = {summary['adversarial_reject']['mean']*100:.1f}% "
          f"(Range: {summary['adversarial_reject']['min']*100:.1f}% - {summary['adversarial_reject']['max']*100:.1f}%)")
    print(f"Benign-Hard Reject: Mean = {summary['benign_hard_reject']['mean']*100:.1f}% "
          f"(Range: {summary['benign_hard_reject']['min']*100:.1f}% - {summary['benign_hard_reject']['max']*100:.1f}%)")
    print(f"Contamination: Mean = {summary['contamination']['mean']*100:.1f}% "
          f"(Range: {summary['contamination']['min']*100:.1f}% - {summary['contamination']['max']*100:.1f}%)")
    print(f"Wrote full results to {LOG_PATH}")
    print("============================================================")


if __name__ == "__main__":
    main()
