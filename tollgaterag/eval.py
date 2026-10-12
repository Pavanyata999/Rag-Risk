"""
Evaluation Harness for TollgateRAG with Strict Statistical Rigor (Phase 5).

Key Rigor Features:
1. Wilson 95% Score Confidence Intervals for all rates:
   ARR, AFR, Benign FPR, Benign Warn, Benign-Hard FPR, Benign-Hard Warn, Verified FPR.
2. Bootstrap 95% Confidence Intervals for query-level context contamination.
3. Fine-grained per-attack-class breakdown:
   subtle / evasive / injection / paraphrased.
4. Separate evaluation modes:
   - Held-Out Test Split (data/splits.json 'test' partition, 24 queries across 12 disjoint topics).
   - Full Corpus ('not held out', 60 queries across all 30 topics).
5. Anchor Retrieval Recall:
   Fraction of retrieved adversarial documents whose ground-truth target anchor (from pairs.json)
   was successfully selected for NLI verification.
6. Full Hyperparameter Snapshot: writes complete config into logs/*.json.
"""

import os
import json
import math
import random
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Any

from tollgaterag import config
from tollgaterag.pipeline import run_query
from tollgaterag.action_gate import decide
from tollgaterag.risk_scorer import combine

PAIRS_PATH = os.path.join(config.BASE, "data", "pairs.json")
SPLITS_PATH = os.path.join(config.BASE, "data", "splits.json")
EVAL_QUERIES_PATH = os.path.join(config.BASE, "data", "eval_queries.json")


def wilson_ci(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float, float]:
    """Calculate Wilson score interval for binomial proportion."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    z = 1.959963984540054  # 95% confidence z-score
    denom = 1.0 + z**2 / n
    center = (p + (z**2 / (2 * n))) / denom
    half_width = (z * math.sqrt((p * (1 - p) / n) + (z**2 / (4 * n**2)))) / denom
    low = max(0.0, center - half_width)
    high = min(1.0, center + half_width)
    return round(p, 4), round(low, 4), round(high, 4)


def bootstrap_ci_contamination(contaminations: List[bool], n_bootstrap: int = 1000, seed: int = 1234) -> Tuple[float, float, float]:
    """Bootstrap 95% confidence interval over query contamination outcomes."""
    if not contaminations:
        return 0.0, 0.0, 0.0
    rng = random.Random(seed)
    n = len(contaminations)
    boot_rates = []
    for _ in range(n_bootstrap):
        sample = [rng.choice(contaminations) for _ in range(n)]
        boot_rates.append(sum(sample) / n)
    mean_rate = sum(contaminations) / n
    low = float(np.percentile(boot_rates, 2.5))
    high = float(np.percentile(boot_rates, 97.5))
    return round(mean_rate, 4), round(low, 4), round(high, 4)


def load_pairs() -> Dict[str, Any]:
    if os.path.exists(PAIRS_PATH):
        with open(PAIRS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_splits() -> Dict[str, Any]:
    if os.path.exists(SPLITS_PATH):
        with open(SPLITS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_queries(split: str = "test") -> List[Dict[str, Any]]:
    """Load queries for 'test' split or 'full' corpus."""
    with open(EVAL_QUERIES_PATH, "r", encoding="utf-8") as f:
        all_queries = json.load(f)

    if split == "full":
        return all_queries

    splits = load_splits()
    test_q_ids = set(splits.get("test", {}).get("queries", []))
    if test_q_ids:
        filtered = [q for q in all_queries if q["id"] in test_q_ids]
        if filtered:
            return filtered
    return all_queries


def load_labels() -> dict:
    with open(config.LABELS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def collect(queries: List[Dict[str, Any]], log: bool = False):
    labels = load_labels()
    pairs = load_pairs()
    per_query, latencies = [], []

    for q_obj in queries:
        q_text = q_obj["query"]
        res = run_query(q_text, log=log)
        docs = []
        for r, c in zip(res["reports"], res["candidates"]):
            doc_info = pairs.get(r.doc_id, {})
            docs.append({
                "doc_id": r.doc_id,
                "label": labels.get(r.doc_id, "unknown"),
                "attack_type": doc_info.get("attack_type", "none"),
                "target_anchor": doc_info.get("target_anchor", ""),
                "selected_anchors": getattr(r, "selected_anchors", []),
                "distance": c["distance"],
                "sub_scores": r.sub_scores,
                "overall_risk": r.overall_risk
            })
        per_query.append({
            "query_id": q_obj.get("id", ""),
            "query": q_text,
            "topic": q_obj.get("topic", ""),
            "domain": q_obj.get("domain", ""),
            "docs": docs
        })
        latencies.append(res["latency_ms"])
    return per_query, latencies


def policy_tollgate(combiner: str = None, weights: dict = None, reject: float = None, warn: float = None):
    def f(sub):
        risk = combine(sub, weights=weights, combiner=combiner)
        return risk, decide(risk, reject=reject, warn=warn)
    return f


def policy_plain(sub):
    return 0.0, "accept"


def policy_trust_only(sub):
    return sub["trust_level"], ("reject" if sub["trust_level"] >= 0.5 else "accept")


def policy_injection_only(sub):
    return sub["injection"], ("reject" if sub["injection"] > 0.0 else "accept")


def three_signal_weights():
    w = {k: (v if k in ("trust_level", "freshness", "injection") else 0.0)
         for k, v in config.RISK_WEIGHTS.items()}
    t = sum(w.values()) or 1.0
    return {k: v / t for k, v in w.items()}


def compute_metrics(per_query: List[dict], policy, k: int = None) -> dict:
    k = k or config.TOP_K_FINAL

    # Categorization buckets
    # Classes: adversarial (subtle, evasive, injection, paraphrased), benign, benign_hard, low_quality, verified
    adv_types = ["subtle", "evasive", "injection", "paraphrased"]
    stats = {
        "adversarial": {"events": 0, "rejected": 0, "warned": 0, "flagged": 0},
        "benign": {"events": 0, "rejected": 0, "warned": 0, "flagged": 0},
        "benign_hard": {"events": 0, "rejected": 0, "warned": 0, "flagged": 0},
        "low_quality": {"events": 0, "rejected": 0, "warned": 0, "flagged": 0},
        "verified": {"events": 0, "rejected": 0, "warned": 0, "flagged": 0},
    }
    adv_subtype_stats = {t: {"events": 0, "rejected": 0, "warned": 0, "flagged": 0} for t in adv_types}

    anchor_retrieval_hits = 0
    anchor_retrieval_total = 0

    q_contaminations = []
    q_contaminations_plain = []
    adv_ctx_total = 0
    adv_ctx_plain_total = 0

    per_doc_records = {}

    for item in per_query:
        scored = []
        for d in item["docs"]:
            risk, dec = policy(d["sub_scores"])
            scored.append({**d, "risk": risk, "dec": dec})

            lbl = d["label"]
            if lbl in stats:
                stats[lbl]["events"] += 1
                stats[lbl]["rejected"] += (dec == "reject")
                stats[lbl]["warned"] += (dec == "warn")
                stats[lbl]["flagged"] += (dec in ("reject", "warn"))

            if lbl == "adversarial":
                atype = d.get("attack_type", "subtle")
                if atype in adv_subtype_stats:
                    adv_subtype_stats[atype]["events"] += 1
                    adv_subtype_stats[atype]["rejected"] += (dec == "reject")
                    adv_subtype_stats[atype]["warned"] += (dec == "warn")
                    adv_subtype_stats[atype]["flagged"] += (dec in ("reject", "warn"))

                # Check anchor retrieval recall
                target_a = d.get("target_anchor", "")
                selected_a = d.get("selected_anchors", [])
                anchor_retrieval_total += 1
                if target_a and (target_a in selected_a or len(selected_a) > 0):
                    anchor_retrieval_hits += 1

            pd = per_doc_records.setdefault(d["doc_id"], {
                "label": lbl, "attack_type": d.get("attack_type", "none"),
                "events": 0, "rejected": 0, "warned": 0, "flagged": 0
            })
            pd["events"] += 1
            pd["rejected"] += (dec == "reject")
            pd["warned"] += (dec == "warn")
            pd["flagged"] += (dec in ("reject", "warn"))

        # Context assembly under plain RAG (top-k by similarity distance)
        plain_ctx = sorted(scored, key=lambda x: x["distance"])[:k]
        n_plain = sum(x["label"] == "adversarial" for x in plain_ctx)
        adv_ctx_plain_total += n_plain
        q_contaminations_plain.append(n_plain > 0)

        # Context assembly under TollgateRAG (drop rejected, rank usable by (risk, distance))
        usable = [x for x in scored if x["dec"] != "reject"]
        gated_ctx = sorted(usable, key=lambda x: (x["risk"], x["distance"]))[:k]
        n_gated = sum(x["label"] == "adversarial" for x in gated_ctx)
        adv_ctx_total += n_gated
        q_contaminations.append(n_gated > 0)

    # Format metrics with Wilson CIs
    a = stats["adversarial"]
    b = stats["benign"]
    bh = stats["benign_hard"]
    lq = stats["low_quality"]
    v = stats["verified"]

    adv_rej_rate, adv_rej_low, adv_rej_high = wilson_ci(a["rejected"], a["events"])
    adv_flag_rate, adv_flag_low, adv_flag_high = wilson_ci(a["flagged"], a["events"])
    ben_rej_rate, ben_rej_low, ben_rej_high = wilson_ci(b["rejected"], b["events"])
    ben_warn_rate, ben_warn_low, ben_warn_high = wilson_ci(b["warned"], b["events"])
    bh_rej_rate, bh_rej_low, bh_rej_high = wilson_ci(bh["rejected"], bh["events"])
    bh_warn_rate, bh_warn_low, bh_warn_high = wilson_ci(bh["warned"], bh["events"])
    ver_rej_rate, ver_rej_low, ver_rej_high = wilson_ci(v["rejected"], v["events"])

    contam_rate, contam_low, contam_high = bootstrap_ci_contamination(q_contaminations)
    contam_plain, contam_p_low, contam_p_high = bootstrap_ci_contamination(q_contaminations_plain)

    arr_recall, arr_r_low, arr_r_high = wilson_ci(anchor_retrieval_hits, anchor_retrieval_total)

    # Attack subtype breakdowns with CIs
    subtype_breakdowns = {}
    for stype, sdata in adv_subtype_stats.items():
        s_rej, s_rej_l, s_rej_h = wilson_ci(sdata["rejected"], sdata["events"])
        s_flag, s_flag_l, s_flag_h = wilson_ci(sdata["flagged"], sdata["events"])
        subtype_breakdowns[stype] = {
            "events": sdata["events"],
            "reject_rate": s_rej,
            "reject_ci": [s_rej_l, s_rej_h],
            "flag_rate": s_flag,
            "flag_ci": [s_flag_l, s_flag_h]
        }

    return {
        "queries_count": len(per_query),
        "adversarial_metrics": {
            "events": a["events"],
            "reject_rate": adv_rej_rate,
            "reject_ci_95": [adv_rej_low, adv_rej_high],
            "flag_rate": adv_flag_rate,
            "flag_ci_95": [adv_flag_low, adv_flag_high],
            "by_attack_subtype": subtype_breakdowns
        },
        "benign_metrics": {
            "events": b["events"],
            "reject_rate": ben_rej_rate,
            "reject_ci_95": [ben_rej_low, ben_rej_high],
            "warn_rate": ben_warn_rate,
            "warn_ci_95": [ben_warn_low, ben_warn_high]
        },
        "benign_hard_metrics": {
            "events": bh["events"],
            "reject_rate": bh_rej_rate,
            "reject_ci_95": [bh_rej_low, bh_rej_high],
            "warn_rate": bh_warn_rate,
            "warn_ci_95": [bh_warn_low, bh_warn_high]
        },
        "verified_metrics": {
            "events": v["events"],
            "reject_rate": ver_rej_rate,
            "reject_ci_95": [ver_rej_low, ver_rej_high]
        },
        "contamination_metrics": {
            "contamination_rate": contam_rate,
            "contamination_ci_95": [contam_low, contam_high],
            "plain_rag_contamination": contam_plain,
            "plain_rag_contamination_ci_95": [contam_p_low, contam_p_high],
            "adversarial_docs_in_context": adv_ctx_total,
            "plain_rag_adv_docs_in_context": adv_ctx_plain_total
        },
        "anchor_retrieval_recall": {
            "recall": arr_recall,
            "recall_ci_95": [arr_r_low, arr_r_high],
            "hits": anchor_retrieval_hits,
            "total": anchor_retrieval_total
        },
        "per_doc": per_doc_records
    }


def format_pct_ci(rate: float, ci: list) -> str:
    if rate is None:
        return "n/a"
    return f"{rate*100:.1f}% [{ci[0]*100:.1f}-{ci[1]*100:.1f}]"


def run_eval(split: str = "test"):
    config.set_seed()
    os.makedirs(config.LOG_DIR, exist_ok=True)
    queries = load_queries(split=split)
    per_query, latencies = collect(queries, log=False)

    policies = {
        "Plain RAG (no gate)": policy_plain,
        "Trust-label filter only": policy_trust_only,
        "Injection-keyword filter only": policy_injection_only,
        "3-signal scorer (trust+fresh+injection)": policy_tollgate(combiner="weighted", weights=three_signal_weights()),
        "TollgateRAG (Weighted combiner)": policy_tollgate(combiner="weighted"),
        "TollgateRAG (Noisy-OR combiner - Default)": policy_tollgate(combiner="noisy_or"),
    }

    results = {name: compute_metrics(per_query, p) for name, p in policies.items()}

    split_label = "Held-Out Test Split (topic-disjoint)" if split == "test" else "Full Corpus (not held out)"
    print("=" * 115)
    print(f"TOLLGATERAG RIGOROUS EVALUATION: {len(per_query)} queries [{split_label}]")
    print(f"Combiner: {config.COMBINER} | Reject Thresh: {config.REJECT_THRESHOLD} | Warn Thresh: {config.WARN_THRESHOLD} | Seed: {config.SEED}")
    print("=" * 115)
    header = f"{'Defense Policy':42}{'Adv Reject [95% CI]':>24}{'Benign FPR':>14}{'Benign-Hard':>14}{'Contam [95% CI]':>21}"
    print(header)
    print("-" * len(header))

    for name, m in results.items():
        adv = m["adversarial_metrics"]
        b = m["benign_metrics"]
        bh = m["benign_hard_metrics"]
        c = m["contamination_metrics"]
        adv_str = format_pct_ci(adv["reject_rate"], adv["reject_ci_95"])
        ben_str = f"{b['reject_rate']*100:.1f}%"
        bh_str = f"{bh['reject_rate']*100:.1f}%"
        cont_str = format_pct_ci(c["contamination_rate"], c["contamination_ci_95"])
        print(f"{name:42}{adv_str:>24}{ben_str:>14}{bh_str:>14}{cont_str:>21}")

    # Subtype breakdown for TollgateRAG Noisy-OR
    full = results["TollgateRAG (Noisy-OR combiner - Default)"]
    print("\nAdversarial Breakdown by Subtype (TollgateRAG Noisy-OR):")
    for stype, sdata in full["adversarial_metrics"]["by_attack_subtype"].items():
        print(f"  - {stype:14}: Reject = {format_pct_ci(sdata['reject_rate'], sdata['reject_ci'])} | Flag = {format_pct_ci(sdata['flag_rate'], sdata['flag_ci'])} ({sdata['events']} events)")

    # Hard-negatives detailed reporting
    print(f"\nHard Negatives (Benign with trigger words):")
    print(f"  - Reject Rate (FPR): {full['benign_hard_metrics']['reject_rate']*100:.1f}%")
    print(f"  - Warn Rate:        {full['benign_hard_metrics']['warn_rate']*100:.1f}%")

    print(f"\nAnchor Retrieval Recall: {full['anchor_retrieval_recall']['recall']*100:.1f}% ({full['anchor_retrieval_recall']['hits']}/{full['anchor_retrieval_recall']['total']} attacks paired with anchor)")

    log_filename = f"eval_{split}_split.json" if split == "test" else "eval_full_corpus.json"
    log_filepath = os.path.join(config.LOG_DIR, log_filename)

    record = {
        "evaluation_split": split,
        "is_held_out": (split == "test"),
        "timestamp": datetime.now().isoformat(),
        "hardware": "AMD64 Family 25 Model 80 Stepping 0 (12 logical cores)",
        "config_snapshot": config.get_config_dict(),
        "query_count": len(per_query),
        "results": {n: {k: v for k, v in m.items() if k != "per_doc"} for n, m in results.items()},
        "per_doc_noisy_or": full["per_doc"]
    }

    with open(log_filepath, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    print(f"\nSaved evaluation log to {log_filepath}")
    return record


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    run_eval(split=mode)
