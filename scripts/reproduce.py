#!/usr/bin/env python3
"""
TollgateRAG Complete Reproducibility Runner.
Runs the entire experimental pipeline from synthetic data generation to paper figures:
1. Pre-flight secrets check
2. Benchmark dataset generation & validation splits
3. Corpus ingestion & vector store indexing
4. Main gating evaluation (TollgateRAG 5-signal with CIs)
5. SOTA comparative baselines evaluation
6. Leave-one-out ablation & threshold sensitivity sweeps
7. Adaptive red-teaming evasion evaluation
8. Publication figures generation
9. Full unit and regression test suite
"""

import os
import sys
import subprocess
import time

STEPS = [
    ("Pre-flight Security Audit", [sys.executable, "scripts/check_no_secrets.py"]),
    ("Generate Benchmark Corpus & Splits", [sys.executable, "scripts/generate_large_benchmark.py"]),
    ("Ingest Corpus into Vector Index", [sys.executable, "-m", "tollgaterag.ingest"]),
    ("Calibrate Thresholds on Validation Split", [sys.executable, "-m", "tollgaterag.calibrate"]),
    ("Evaluate TollgateRAG on Test Split", [sys.executable, "-m", "tollgaterag.eval"]),
    ("Evaluate SOTA Baselines", [sys.executable, "-m", "tollgaterag.eval_baselines"]),
    ("Run Systematic Ablations & Sweeps", [sys.executable, "-m", "tollgaterag.ablation"]),
    ("Run Adaptive Red-Teaming Loop", [sys.executable, "-m", "tollgaterag.red_team"]),
    ("Evaluate PoisonedRAG Harness", [sys.executable, "-m", "tollgaterag.eval_poisonedrag"]),
    ("Generate Publication Vector Figures", [sys.executable, "scripts/generate_paper_figures.py"]),
    ("Run Test Suite", [sys.executable, "-m", "pytest", "tests/", "-q"]),
]

def main():
    os.makedirs("logs", exist_ok=True)
    print("=" * 70)
    print("  TOLLGATERAG: REPRODUCIBILITY PIPELINE EXECUTION")
    print(f"  Reference Date: 2026-10-12 | Random Seed: 1234")
    print("=" * 70)
    start_total = time.time()
    
    for idx, (name, cmd) in enumerate(STEPS, 1):
        print(f"\n[{idx}/{len(STEPS)}] Running: {name} ...")
        t0 = time.time()
        res = subprocess.run(cmd)
        elapsed = time.time() - t0
        if res.returncode != 0:
            print(f"❌ FAILED: {name} (exit code {res.returncode}) after {elapsed:.2f}s")
            return res.returncode
        print(f"✅ PASSED: {name} ({elapsed:.2f}s)")
        
    total_elapsed = time.time() - start_total
    print("\n" + "=" * 70)
    print(f"🎉 SUCCESS: Pipeline completed in {total_elapsed:.2f}s.")
    print("All outputs, metrics, and figures written to logs/ and docs/paper/figures/.")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
