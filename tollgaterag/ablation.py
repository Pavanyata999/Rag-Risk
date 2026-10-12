"""
Comprehensive Ablation Suite and Threshold Sweep for TollgateRAG.

Evaluates:
1. Leave-one-out risk dimension ablation reporting BOTH:
   - Zeroed weight (no renormalization artifact)
   - Renormalized weight
2. Architectural ablations:
   - Combiner comparison: Noisy-OR vs. Weighted sum
   - Neural NLI vs. Heuristic cues: USE_NLI off, USE_CUE_FALLBACK off
   - Anchor selection variants: top-1, top-2, top-3 (default), top-5, and Oracle Anchor
3. Threshold sweep:
   - Evaluated on the held-out VALIDATION split to prevent test contamination
   - Final operating point evaluated on the held-out TEST split
"""

import os
import json
import numpy as np
from typing import Dict, List, Any
from tollgaterag import config
from tollgaterag.retriever import Retriever
from tollgaterag.risk_scorer import score_candidates, combine, _anchor_conflict
from tollgaterag.action_gate import decide
from tollgaterag.eval import (
    load_queries,
    load_labels,
    load_splits,
    load_pairs,
    compute_metrics,
    wilson_ci
)
from tollgaterag.calibrate import load_val_documents

OUT_PATH = os.path.join(config.LOG_DIR, "ablation_results.json")


def run_ablation_suite():
    config.set_seed()
    labels = load_labels()
    splits = load_splits()
    pairs = load_pairs()
    retriever = Retriever()
    anchors = retriever.verified_anchors()

    test_queries = load_queries("test")
    print(f"Collecting test candidates using standard eval pipeline ({len(test_queries)} queries)...")
    from tollgaterag.eval import collect
    per_query_test, _ = collect(test_queries, log=False)

    def extract_summary(m):
        return {
            "events": m["adversarial_metrics"]["events"],
            "adv_reject_rate": m["adversarial_metrics"]["reject_rate"],
            "adv_reject_ci": m["adversarial_metrics"]["reject_ci_95"],
            "benign_events": m["benign_metrics"]["events"],
            "benign_reject_rate": m["benign_metrics"]["reject_rate"],
            "benign_hard_events": m["benign_hard_metrics"]["events"],
            "benign_hard_reject_rate": m["benign_hard_metrics"]["reject_rate"],
            "contamination": m["contamination_metrics"]["contamination_rate"]
        }

    # Helper policy evaluator
    def eval_policy(per_q, policy_fn):
        m = compute_metrics(per_q, policy_fn)
        return extract_summary(m)

    print("=" * 115)
    print("PART 1: LEAVE-ONE-OUT RISK DIMENSION ABLATION (Held-Out Test Split)")
    print("=" * 115)
    header = f"{'Configuration':40}{'Weight Scheme':18}{'Adv Reject':>12}{'Benign FP':>12}{'Contam.':>11}"
    print(header)
    print("-" * len(header))

    base_weights = dict(config.RISK_WEIGHTS)
    leave_one_out_results = []

    # Baseline: Full model
    full_m = eval_policy(per_query_test, lambda sub: (combine(sub), decide(combine(sub))))
    print(f"{'Full Model (Default Noisy-OR)':40}{'Nominal':18}{full_m['adv_reject_rate']*100:>11.1f}%{full_m['benign_reject_rate']*100:>11.1f}%{full_m['contamination']*100:>10.1f}%")
    leave_one_out_results.append({
        "configuration": "Full Model (Default Noisy-OR)",
        "weight_scheme": "nominal",
        **full_m
    })

    # Dimensions to ablate
    dims = ["anchor_conflict", "injection", "trust_level", "authority_claim", "freshness"]

    for dim in dims:
        # A. Zeroed Weight (No renormalization)
        zeroed_w = {k: (0.0 if k == dim else v) for k, v in base_weights.items()}
        m_zero = eval_policy(per_query_test, lambda sub: (combine(sub, weights=zeroed_w), decide(combine(sub, weights=zeroed_w))))
        print(f"{f'without {dim}':40}{'zeroed (unnorm)':18}{m_zero['adv_reject_rate']*100:>11.1f}%{m_zero['benign_reject_rate']*100:>11.1f}%{m_zero['contamination']*100:>10.1f}%")
        leave_one_out_results.append({
            "configuration": f"without {dim}",
            "weight_scheme": "zeroed_unnormalized",
            "adv_reject_rate": m_zero["adv_reject_rate"],
            "adv_reject_ci": m_zero["adv_reject_ci"],
            "benign_reject_rate": m_zero["benign_reject_rate"],
            "contamination": m_zero["contamination"]
        })

        # B. Renormalized Weight
        rem_sum = sum(base_weights[k] for k in base_weights if k != dim) or 1.0
        renorm_w = {k: (0.0 if k == dim else v / rem_sum) for k, v in base_weights.items()}
        m_renorm = eval_policy(per_query_test, lambda sub: (combine(sub, weights=renorm_w), decide(combine(sub, weights=renorm_w))))
        print(f"{f'without {dim}':40}{'renormalized':18}{m_renorm['adv_reject_rate']*100:>11.1f}%{m_renorm['benign_reject_rate']*100:>11.1f}%{m_renorm['contamination']*100:>10.1f}%")
        leave_one_out_results.append({
            "configuration": f"without {dim}",
            "weight_scheme": "renormalized",
            "adv_reject_rate": m_renorm["adv_reject_rate"],
            "adv_reject_ci": m_renorm["adv_reject_ci"],
            "benign_reject_rate": m_renorm["benign_reject_rate"],
            "contamination": m_renorm["contamination"]
        })

    print("\n" + "=" * 115)
    print("PART 2: ARCHITECTURAL ABLATIONS (Held-Out Test Split)")
    print("=" * 115)
    header = f"{'Architectural Variant':45}{'Adv Reject':>12}{'Benign FP':>12}{'Contam.':>11}"
    print(header)
    print("-" * len(header))

    arch_results = []

    # 1. Combiner: Weighted Sum
    m_weighted = eval_policy(per_query_test, lambda sub: (combine(sub, combiner="weighted"), decide(combine(sub, combiner="weighted"))))
    print(f"{'Combiner: Weighted Sum (Legacy)':45}{m_weighted['adv_reject_rate']*100:>11.1f}%{m_weighted['benign_reject_rate']*100:>11.1f}%{m_weighted['contamination']*100:>10.1f}%")
    arch_results.append({"variant": "Combiner: Weighted Sum", **{k: v for k, v in m_weighted.items() if k != "per_doc"}})

    # 2. USE_NLI off (Cue fallback only)
    def re_score_queries(use_nli=True, use_cue=True, max_pairs=3, oracle=False):
        re_scored = []
        old_nli = config.USE_NLI
        old_cue = config.USE_CUE_FALLBACK
        config.USE_NLI = use_nli
        config.USE_CUE_FALLBACK = use_cue
        try:
            for item in per_query_test:
                new_docs = []
                for d in item["docs"]:
                    c = d["raw_candidate"]
                    if oracle:
                        # Find exact target anchor
                        t_anchor_id = d["target_anchor"]
                        eval_anchors = [a for a in anchors if a["id"] == t_anchor_id] or anchors
                    else:
                        eval_anchors = anchors
                    
                    score, _, sel_ids, _ = _anchor_conflict(c, eval_anchors, max_pairs=max_pairs)
                    new_sub = dict(d["sub_scores"])
                    new_sub["anchor_conflict"] = score
                    new_docs.append({**d, "sub_scores": new_sub, "selected_anchors": sel_ids})
                re_scored.append({"query": item["query"], "docs": new_docs})
        finally:
            config.USE_NLI = old_nli
            config.USE_CUE_FALLBACK = old_cue
        return re_scored

    print("Computing NLI / Cue / Pair ablations...")
    # USE_NLI off
    q_no_nli = re_score_queries(use_nli=False, use_cue=True)
    m_no_nli = eval_policy(q_no_nli, lambda sub: (combine(sub), decide(combine(sub))))
    print(f"{'Ablation: USE_NLI off (Cue fallback only)':45}{m_no_nli['adv_reject_rate']*100:>11.1f}%{m_no_nli['benign_reject_rate']*100:>11.1f}%{m_no_nli['contamination']*100:>10.1f}%")
    arch_results.append({"variant": "Ablation: USE_NLI off", **{k: v for k, v in m_no_nli.items() if k != "per_doc"}})

    # USE_CUE_FALLBACK off
    q_no_cue = re_score_queries(use_nli=True, use_cue=False)
    m_no_cue = eval_policy(q_no_cue, lambda sub: (combine(sub), decide(combine(sub))))
    print(f"{'Ablation: USE_CUE_FALLBACK off (Neural NLI only)':45}{m_no_cue['adv_reject_rate']*100:>11.1f}%{m_no_cue['benign_reject_rate']*100:>11.1f}%{m_no_cue['contamination']*100:>10.1f}%")
    arch_results.append({"variant": "Ablation: USE_CUE_FALLBACK off", **{k: v for k, v in m_no_cue.items() if k != "per_doc"}})

    # Anchor pair variants: top-1, top-2, top-3, top-5, oracle
    for pairs_k in [1, 2, 3, 5]:
        q_pairs = re_score_queries(use_nli=True, use_cue=True, max_pairs=pairs_k)
        m_pairs = eval_policy(q_pairs, lambda sub: (combine(sub), decide(combine(sub))))
        print(f"{f'Anchor selection: top-{pairs_k} sentence pairs':45}{m_pairs['adv_reject_rate']*100:>11.1f}%{m_pairs['benign_reject_rate']*100:>11.1f}%{m_pairs['contamination']*100:>10.1f}%")
        arch_results.append({"variant": f"Anchor selection: top-{pairs_k} pairs", **{k: v for k, v in m_pairs.items() if k != "per_doc"}})

    # Oracle anchor
    q_oracle = re_score_queries(use_nli=True, use_cue=True, oracle=True)
    m_oracle = eval_policy(q_oracle, lambda sub: (combine(sub), decide(combine(sub))))
    print(f"{'Anchor selection: Oracle Anchor':45}{m_oracle['adv_reject_rate']*100:>11.1f}%{m_oracle['benign_reject_rate']*100:>11.1f}%{m_oracle['contamination']*100:>10.1f}%")
    arch_results.append({"variant": "Anchor selection: Oracle Anchor", **{k: v for k, v in m_oracle.items() if k != "per_doc"}})

    print("\n" + "=" * 115)
    print("PART 3A: ANCHOR SELECTION CALIBRATION ON VALIDATION SPLIT (max_pairs in [1, 2, 3, 5])")
    print("=" * 115)
    val_docs = load_val_documents()
    val_anchor_sweep = []
    chosen_pairs_k = 3
    best_val_arr = -1.0
    for pk in [1, 2, 3, 5]:
        val_re_scored = []
        for d in val_docs:
            sc, _, _, _ = _anchor_conflict(d, anchors, max_pairs=pk)
            sub = {
                "trust_level": 0.05 if d["label"] == "verified" else 0.55,
                "freshness": 0.1,
                "injection": 0.0,
                "authority_claim": 0.0,
                "anchor_conflict": sc
            }
            r_val = combine(sub)
            val_re_scored.append((r_val, d["label"]))
        val_arr_k = sum(1 for s, l in val_re_scored if l == "adversarial" and s >= config.REJECT_THRESHOLD) / max(1, sum(1 for _, l in val_re_scored if l == "adversarial"))
        val_fpr_k = sum(1 for s, l in val_re_scored if l == "benign" and s >= config.REJECT_THRESHOLD) / max(1, sum(1 for _, l in val_re_scored if l == "benign"))
        val_anchor_sweep.append({
            "max_pairs": pk,
            "val_adversarial_reject_rate": round(val_arr_k, 4),
            "val_clean_benign_fpr": round(val_fpr_k, 4)
        })
        print(f"max_pairs={pk}: Val ARR={val_arr_k*100:.1f}%, Val Clean FPR={val_fpr_k*100:.1f}%")
        if val_fpr_k <= 0.02 and val_arr_k > best_val_arr:
            best_val_arr = val_arr_k
            chosen_pairs_k = pk
    print(f"Chosen anchor selection setting on validation split: max_pairs={chosen_pairs_k}")

    print("\n" + "=" * 115)
    print("PART 3B: THRESHOLD SWEEP ON VALIDATION SPLIT (0.20 to 0.70)")
    print("=" * 115)
    # Load validation documents
    val_docs = load_val_documents()
    val_reports = score_candidates(val_docs, anchors)
    scored_val = [(r.overall_risk, d["label"]) for r, d in zip(val_reports, val_docs)]

    val_adv_count = sum(1 for _, l in scored_val if l == "adversarial")
    val_ben_count = sum(1 for _, l in scored_val if l == "benign")
    val_hard_count = sum(1 for _, l in scored_val if l == "benign_hard")

    sweep_curve = []
    print(f"{'Reject Thresh':>14}{'Warn Thresh':>14}{'Val ARR':>12}{'Val Benign FP':>16}{'Val Hard FP':>14}")
    print("-" * 75)
    for rej in np.linspace(0.20, 0.70, 11):
        rej = round(float(rej), 2)
        warn = round(max(0.15, rej - 0.20), 2)
        
        arr = sum(1 for s, l in scored_val if l == "adversarial" and s >= rej) / max(val_adv_count, 1)
        fpr = sum(1 for s, l in scored_val if l == "benign" and s >= rej) / max(val_ben_count, 1)
        hard_fpr = sum(1 for s, l in scored_val if l == "benign_hard" and s >= rej) / max(val_hard_count, 1)

        sweep_curve.append({
            "reject_threshold": rej,
            "warn_threshold": warn,
            "val_adversarial_reject_rate": round(arr, 4),
            "val_clean_benign_fpr": round(fpr, 4),
            "val_benign_hard_fpr": round(hard_fpr, 4)
        })
        print(f"{rej:>14.2f}{warn:>14.2f}{arr*100:>11.1f}%{fpr*100:>15.1f}%{hard_fpr*100:>13.1f}%")

    out_data = {
        "metadata": {
            "test_query_count": len(test_queries),
            "validation_document_count": len(val_docs),
            "config": config.get_config_dict()
        },
        "leave_one_out_ablation": leave_one_out_results,
        "architectural_ablations": arch_results,
        "chosen_anchor_max_pairs": chosen_pairs_k,
        "validation_anchor_selection_sweep": val_anchor_sweep,
        "validation_threshold_sweep": sweep_curve,
        "test_operating_point": {
            "reject_threshold": config.REJECT_THRESHOLD,
            "warn_threshold": config.WARN_THRESHOLD,
            "adv_reject_rate": full_m["adv_reject_rate"],
            "adv_reject_ci": full_m["adv_reject_ci"],
            "benign_reject_rate": full_m["benign_reject_rate"],
            "benign_hard_reject_rate": full_m["benign_hard_reject_rate"],
            "contamination": full_m["contamination"]
        }
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)
    print(f"\nSaved complete ablation suite results to: {OUT_PATH}")
    return out_data


if __name__ == "__main__":
    run_ablation_suite()
