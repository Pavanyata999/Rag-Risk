"""
Latency Benchmarking Module for TollgateRAG.
Measures cold-start vs. warm inference latency across pipeline stages:
Retrieval, Anchor Selection, Sentence NLI Scoring, Gating, and Generation.

Logs median, p95, mean, min, max, and exact hardware specs to logs/latency_benchmark.json.
"""

import os
import sys
import json
import time
import platform
import numpy as np

from tollgaterag import config
from tollgaterag.pipeline import run_query
from tollgaterag.eval import load_queries

LOG_PATH = os.path.join(config.BASE, "logs", "latency_benchmark.json")


def get_hardware_info() -> dict:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count_logical": os.cpu_count(),
        "python_version": sys.version.split()[0]
    }


def run_latency_benchmark(num_warm_queries: int = 30):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    raw_queries = load_queries()
    queries = [q["query"] if isinstance(q, dict) else q for q in raw_queries]
    if not queries:
        queries = ["What is the international travel expense policy?"]

    # 1. Measure Cold Start Latency (first query, unloaded models)
    print("Running Cold Start measurement...")
    t_cold_start = time.perf_counter()
    res_cold = run_query(queries[0], log=False)
    cold_total_ms = (time.perf_counter() - t_cold_start) * 1000

    cold_result = {
        "total_ms": round(cold_total_ms, 2),
        "breakdown": res_cold.get("timing_breakdown", {})
    }
    print(f"  Cold Start Latency: {cold_total_ms:.1f} ms")

    # 2. Measure Warm Latency across repeated queries
    print(f"Running Warm Benchmarking across {num_warm_queries} queries...")
    warm_totals = []
    stage_latencies = {
        "retrieval_ms": [],
        "anchor_selection_ms": [],
        "scoring_nli_ms": [],
        "gating_ms": [],
        "generation_ms": []
    }

    warm_pool = (queries * ((num_warm_queries // len(queries)) + 2))[:num_warm_queries]
    for idx, q in enumerate(warm_pool, 1):
        res = run_query(q, log=False)
        bd = res.get("timing_breakdown", {})
        warm_totals.append(bd.get("total_ms", res.get("latency_ms", 0.0)))
        for stage in stage_latencies:
            if stage in bd:
                stage_latencies[stage].append(bd[stage])

    warm_stats = {
        "count": len(warm_totals),
        "mean_ms": round(float(np.mean(warm_totals)), 2),
        "median_ms": round(float(np.median(warm_totals)), 2),
        "p95_ms": round(float(np.percentile(warm_totals, 95)), 2),
        "min_ms": round(float(np.min(warm_totals)), 2),
        "max_ms": round(float(np.max(warm_totals)), 2),
        "stage_breakdown_median_ms": {
            stage: round(float(np.median(vals)), 2) for stage, vals in stage_latencies.items() if vals
        },
        "stage_breakdown_p95_ms": {
            stage: round(float(np.percentile(vals, 95)), 2) for stage, vals in stage_latencies.items() if vals
        },
        "stage_breakdown_mean_ms": {
            stage: round(float(np.mean(vals)), 2) for stage, vals in stage_latencies.items() if vals
        }
    }

    print(f"  Warm Median: {warm_stats['median_ms']:.1f} ms | p95: {warm_stats['p95_ms']:.1f} ms | Mean: {warm_stats['mean_ms']:.1f} ms")

    benchmark_record = {
        "hardware": get_hardware_info(),
        "config": config.get_config_dict(),
        "cold_start": cold_result,
        "warm_runs": warm_stats
    }

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(benchmark_record, f, indent=2)

    print(f"Saved benchmark results to {LOG_PATH}")
    return benchmark_record


if __name__ == "__main__":
    run_latency_benchmark()
