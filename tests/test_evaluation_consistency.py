"""
Regression test suite for evaluation population reconciliation, denominator consistency,
statistical confidence intervals, and judge agreement computation.
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tollgaterag import config
from tollgaterag.eval import wilson_ci
from scripts.judge_agreement import compute_cohens_kappa


def test_wilson_ci_bounds():
    """Verify Wilson score confidence interval properties."""
    # 0 out of 79
    mid, low, high = wilson_ci(0, 79)
    assert low == 0.0
    assert 0.04 < high < 0.05
    assert low <= mid <= high

    # 70 out of 79 (88.6%)
    mid, low, high = wilson_ci(70, 79)
    assert round(mid, 3) == 0.886
    assert 0.79 < low < 0.81
    assert 0.93 < high < 0.95

    # 79 out of 79 (100%)
    mid, low, high = wilson_ci(79, 79)
    assert high == 1.0
    assert 0.95 < low < 0.96


def test_sota_baseline_denominators_reconciled():
    """Verify all baselines in logs/sota_baselines_comparison.json evaluate identical sample populations."""
    log_path = os.path.join(config.LOG_DIR, "sota_baselines_comparison.json")
    assert os.path.exists(log_path), f"Missing {log_path}"

    with open(log_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", {})
    assert len(results) >= 8, f"Expected at least 8 baselines, got {len(results)}"

    # Every baseline must evaluate exactly 79 adversarial, 13 benign, 12 benign-hard events
    for name, m in results.items():
        breakdown = m.get("events_breakdown", {})
        adv_events = breakdown.get("adversarial", {}).get("events")
        benign_events = breakdown.get("benign", {}).get("events")
        hard_events = breakdown.get("benign_hard", {}).get("events")

        assert adv_events == 79, f"{name}: expected 79 adversarial events, got {adv_events}"
        assert benign_events == 13, f"{name}: expected 13 clean benign events, got {benign_events}"
        assert hard_events == 12, f"{name}: expected 12 benign-hard events, got {hard_events}"


def test_primary_and_baseline_tollgaterag_match():
    """Verify primary TollgateRAG evaluation and baseline TollgateRAG evaluation report identical metrics."""
    sota_path = os.path.join(config.LOG_DIR, "sota_baselines_comparison.json")
    eval_path = os.path.join(config.LOG_DIR, "eval_test_split.json")

    with open(sota_path, "r", encoding="utf-8") as f:
        sota = json.load(f)["results"]["8. TollgateRAG (Noisy-OR NLI Gate)"]

    with open(eval_path, "r", encoding="utf-8") as f:
        primary = json.load(f)["results"]["TollgateRAG (Noisy-OR combiner - Default)"]

    # Adversarial rejection rate
    assert abs(sota["adv_reject_rate"] - primary["adversarial_metrics"]["reject_rate"]) < 1e-4
    prim_adv_rejected = round(primary["adversarial_metrics"]["events"] * primary["adversarial_metrics"]["reject_rate"])
    assert sota["events_breakdown"]["adversarial"]["rejected"] == prim_adv_rejected == 70
    assert sota["events_breakdown"]["adversarial"]["events"] == primary["adversarial_metrics"]["events"] == 79

    # Clean Benign FPR
    assert abs(sota["benign_reject_rate"] - primary["benign_metrics"]["reject_rate"]) < 1e-4
    prim_benign_rejected = round(primary["benign_metrics"]["events"] * primary["benign_metrics"]["reject_rate"])
    assert sota["events_breakdown"]["benign"]["rejected"] == prim_benign_rejected == 0
    assert sota["events_breakdown"]["benign"]["events"] == primary["benign_metrics"]["events"] == 13

    # Benign-Hard FPR
    assert abs(sota["benign_hard_reject_rate"] - primary["benign_hard_metrics"]["reject_rate"]) < 1e-4
    prim_hard_rejected = round(primary["benign_hard_metrics"]["events"] * primary["benign_hard_metrics"]["reject_rate"])
    assert sota["events_breakdown"]["benign_hard"]["rejected"] == prim_hard_rejected == 8
    assert sota["events_breakdown"]["benign_hard"]["events"] == primary["benign_hard_metrics"]["events"] == 12

    # Context contamination
    assert abs(sota["contamination"] - primary["contamination_metrics"]["contamination_rate"]) < 1e-4
    assert abs(sota["contamination"] - 7/24) < 1e-4


def test_strict_whitelist_benign_tradeoff():
    """Verify strict whitelist correctly shows 100% FPR on benign unverified sources."""
    sota_path = os.path.join(config.LOG_DIR, "sota_baselines_comparison.json")
    with open(sota_path, "r", encoding="utf-8") as f:
        whitelist = json.load(f)["results"]["2. Strict Whitelist (Zero Trust)"]

    assert whitelist["adv_reject_rate"] == 1.0
    assert whitelist["benign_reject_rate"] == 1.0, "Strict Whitelist must reject 100% of clean unverified docs"
    assert whitelist["benign_hard_reject_rate"] == 1.0, "Strict Whitelist must reject 100% of benign-hard docs"
    assert whitelist["contamination"] == 0.0


def test_cohens_kappa_calculation():
    """Verify Cohen's kappa calculations on synthetic agreement cases."""
    # Perfect agreement
    labels_a = ["VIOLATION_PRESERVED"] * 20 + ["SAFE_CAPITULATION"] * 20
    labels_b = ["VIOLATION_PRESERVED"] * 20 + ["SAFE_CAPITULATION"] * 20
    p_o, kappa = compute_cohens_kappa(labels_a, labels_b)
    assert p_o == 1.0
    assert kappa == 1.0

    # Complete disagreement
    labels_inv = ["SAFE_CAPITULATION"] * 20 + ["VIOLATION_PRESERVED"] * 20
    p_o_inv, kappa_inv = compute_cohens_kappa(labels_a, labels_inv)
    assert p_o_inv == 0.0
    assert kappa_inv == -1.0

    # Empty inputs
    p_o_empty, kappa_empty = compute_cohens_kappa([], [])
    assert p_o_empty == 0.0
    assert kappa_empty == 0.0
