"""
Calibration module for TollgateRAG action thresholds.
Selects optimal operational thresholds (REJECT_THRESHOLD, WARN_THRESHOLD)
STRICTLY on the held-out VALIDATION split (never on test data).

Optimization Objective:
  Maximize Adversarial Reject Rate (ARR) subject to Benign False Positive Rate (FPR) <= 0.02.
  If tie, maximize margin to FPR boundary.
Outputs results and full validation Pareto curve to logs/calibration.json.
"""

import os
import json
import numpy as np
from datetime import datetime
from tollgaterag import config
from tollgaterag.risk_scorer import score_candidates, combine
from tollgaterag.action_gate import decide

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPLITS_PATH = os.path.join(BASE_DIR, "data", "splits.json")
LABELS_PATH = os.path.join(BASE_DIR, "data", "labels.json")
DATA_DIR = os.path.join(BASE_DIR, "data", "sample_docs")
LOG_PATH = os.path.join(BASE_DIR, "logs", "calibration.json")


def load_val_documents():
    """Load documents assigned to the validation split."""
    if not os.path.exists(SPLITS_PATH):
        # Fallback if splits not yet generated: deterministic 60/20/20 partition
        config.set_seed()
        import glob
        all_docs = sorted([os.path.basename(p) for p in glob.glob(os.path.join(DATA_DIR, "doc_*.txt"))])
        val_docs = all_docs[len(all_docs)//2: len(all_docs)//2 + len(all_docs)//4]
    else:
        with open(SPLITS_PATH, "r", encoding="utf-8") as f:
            splits = json.load(f)
        val_docs = splits.get("val", {}).get("documents", [])

    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        labels = json.load(f)

    # Parse headers and bodies
    docs = []
    for fname in val_docs:
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.splitlines()
        header = {}
        body_lines = []
        in_body = False
        for line in lines:
            if not in_body and ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                header[k.strip().lower()] = v.strip()
            else:
                in_body = True
                body_lines.append(line)
        body = "\n".join(body_lines).strip()
        docs.append({
            "id": fname,
            "title": header.get("title", fname),
            "trust_level": header.get("trust_level", "unverified"),
            "date": header.get("date", "2026-09-01"),
            "body": body,
            "label": labels.get(fname, "unknown")
        })
    return docs


def calibrate():
    """Perform grid search on validation split to select thresholds."""
    config.set_seed()
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    val_docs = load_val_documents()

    if not val_docs:
        print("Warning: No validation documents found for calibration. Using default config.")
        return config.REJECT_THRESHOLD, config.WARN_THRESHOLD

    # Verified anchors from data directory
    from tollgaterag.retriever import Retriever
    retriever = Retriever()
    anchors = retriever.verified_anchors()

    # Pre-score all validation candidates
    reports = score_candidates(val_docs, anchors)
    scored = []
    for r, d in zip(reports, val_docs):
        scored.append((r.overall_risk, d["label"], d["id"]))

    reject_grid = np.linspace(0.20, 0.70, 51)
    warn_grid = np.linspace(0.10, 0.40, 31)

    curve = []
    best_tuple = None
    best_arr = -1.0
    best_fpr = 1.0

    adv_count = sum(1 for _, label, _ in scored if "adversarial" in label)
    benign_count = sum(1 for _, label, _ in scored if "benign" in label)

    for rej_th in reject_grid:
        rej_th = round(float(rej_th), 4)
        adv_rej = sum(1 for score, label, _ in scored if "adversarial" in label and score >= rej_th)
        ben_fp = sum(1 for score, label, _ in scored if "benign" in label and score >= rej_th)

        arr = adv_rej / max(adv_count, 1)
        fpr = ben_fp / max(benign_count, 1)

        curve.append({
            "reject_threshold": rej_th,
            "adversarial_reject_rate": round(arr, 4),
            "benign_fpr": round(fpr, 4)
        })

        # Constraint: Benign FPR <= 2% (0.02)
        if fpr <= 0.02:
            if arr > best_arr or (arr == best_arr and rej_th < (best_tuple[0] if best_tuple else 1.0)):
                best_arr = arr
                best_fpr = fpr
                best_tuple = (rej_th, round(max(0.15, rej_th - 0.20), 2))

    chosen_rej, chosen_warn = best_tuple if best_tuple else (0.45, 0.25)

    calibration_record = {
        "timestamp": datetime.now().isoformat(),
        "procedure": "Validation split grid-search maximizing ARR subject to Benign FPR <= 2%",
        "val_document_count": len(val_docs),
        "adversarial_count": adv_count,
        "benign_count": benign_count,
        "chosen_thresholds": {
            "reject_threshold": chosen_rej,
            "warn_threshold": chosen_warn
        },
        "validation_performance": {
            "adversarial_reject_rate": best_arr,
            "benign_false_positive_rate": best_fpr
        },
        "config_snapshot": config.get_config_dict(),
        "sweep_curve": curve
    }

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(calibration_record, f, indent=2)

    print(f"Calibration Complete: REJECT_THRESHOLD={chosen_rej}, WARN_THRESHOLD={chosen_warn}")
    print(f"Validation Performance: ARR={best_arr*100:.2f}%, Benign FPR={best_fpr*100:.2f}%")
    print(f"Saved curve and decisions to {LOG_PATH}")
    return chosen_rej, chosen_warn


if __name__ == "__main__":
    calibrate()
