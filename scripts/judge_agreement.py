"""
Judge Validation Agreement Script: scripts/judge_agreement.py

Computes observed percentage agreement and Cohen's kappa between the LLM Judge
(qwen/qwen3.8-27b) and human expert labels in data/judge_validation.csv.

Outputs results to logs/judge_agreement.json.
If human_label is empty or incomplete, logs status as "pending_human_annotation".
"""

import os
import sys
import csv
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(BASE_DIR, "data", "judge_validation.csv")
LOG_PATH = os.path.join(BASE_DIR, "logs", "judge_agreement.json")


def compute_cohens_kappa(judge_labels, human_labels):
    """
    Computes Cohen's kappa for binary classification:
    kappa = (P_observed - P_expected) / (1 - P_expected)
    """
    n = len(judge_labels)
    if n == 0:
        return 0.0

    # Normalise labels: 1 for violation/positive, 0 for capitulation/negative
    def norm(lbl):
        s = str(lbl).strip().upper()
        if s in ("1", "TRUE", "VIOLATION_PRESERVED", "VIOLATION", "YES"):
            return 1
        return 0

    j_bin = [norm(x) for x in judge_labels]
    h_bin = [norm(x) for x in human_labels]

    # Observed agreement
    p_o = sum(1 for j, h in zip(j_bin, h_bin) if j == h) / n

    # Marginal probabilities
    j_pos = sum(j_bin) / n
    h_pos = sum(h_bin) / n
    j_neg = 1.0 - j_pos
    h_neg = 1.0 - h_pos

    p_e = (j_pos * h_pos) + (j_neg * h_neg)

    if abs(1.0 - p_e) < 1e-9:
        kappa = 1.0 if p_o == 1.0 else 0.0
    else:
        kappa = (p_o - p_e) / (1.0 - p_e)

    return p_o, kappa


def main():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        sys.exit(1)

    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    total_cases = len(rows)
    annotated = [r for r in rows if r.get("human_label", "").strip() != ""]

    if len(annotated) < total_cases:
        print(f"Judge validation status: PENDING ({len(annotated)}/{total_cases} human labels provided).")
        result = {
            "status": "pending_human_annotation",
            "total_cases": total_cases,
            "annotated_cases": len(annotated),
            "agreement_rate": None,
            "cohens_kappa": None,
            "note": "Human labels in data/judge_validation.csv are not yet filled."
        }
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"Wrote status to {LOG_PATH}")
        return

    # All annotated
    judge_labels = [r["judge_verdict"] for r in rows]
    human_labels = [r["human_label"] for r in rows]

    p_o, kappa = compute_cohens_kappa(judge_labels, human_labels)

    result = {
        "status": "completed",
        "total_cases": total_cases,
        "annotated_cases": len(annotated),
        "agreement_rate": round(p_o, 4),
        "cohens_kappa": round(kappa, 4),
        "judge_model": "qwen/qwen3.8-27b"
    }

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Agreement Rate: {p_o * 100:.1f}%")
    print(f"Cohen's Kappa: {kappa:.3f}")
    print(f"Wrote agreement metrics to {LOG_PATH}")


if __name__ == "__main__":
    main()
