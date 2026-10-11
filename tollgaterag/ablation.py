"""
Ablation + threshold sweep (no re-retrieval needed: sub-scores are cached).

  1. Ablation: zero one dimension at a time, renormalize the others.
  2. Threshold sweep: reject threshold vs. adversarial catch rate and benign
     false-positive rate (the trade-off a deployer actually has to choose).

Run:  python -m tollgaterag.ablation
"""

import json
import os

from tollgaterag import config
from tollgaterag.eval import collect, compute_metrics, policy_tollgate, pct


def run():
    per_query, _ = collect(log=False)
    base = config.RISK_WEIGHTS

    print("=" * 92)
    print("ABLATION: remove one risk dimension (weights renormalized)")
    print("=" * 92)
    print(f"{'Configuration':30}{'AdvReject':>11}{'AdvFlag':>9}{'BenignFP':>10}{'Contam.':>9}{'AdvInCtx':>9}")
    rows = []

    def add(name, weights):
        m = compute_metrics(per_query, policy_tollgate(weights=weights))
        rows.append({"configuration": name, **{k: v for k, v in m.items() if k != "per_doc"}})
        print(f"{name:30}{pct(m['adv_reject_rate']):>11}{pct(m['adv_flag_rate']):>9}"
              f"{pct(m['benign_reject_rate']):>10}{pct(m['contamination']):>9}{m['adv_docs_in_context']:>9}")

    add("Full model", base)
    for dim in base:
        w = {k: (0.0 if k == dim else v) for k, v in base.items()}
        t = sum(w.values())
        add(f"without {dim}", {k: v / t for k, v in w.items()})

    print("\n" + "=" * 92)
    print("THRESHOLD SWEEP (warn threshold = 0.55 x reject threshold)")
    print("=" * 92)
    print(f"{'Reject>=':>9}{'Warn>=':>8}{'AdvReject':>11}{'AdvFlag':>9}{'BenignFP':>10}{'BenignFlag':>11}{'VerifFP':>9}{'Contam.':>9}")
    sweep = []
    reject = 0.20
    while reject <= 0.701:
        warn = round(reject * 0.55, 3)
        m = compute_metrics(per_query, policy_tollgate(reject=reject, warn=warn))
        sweep.append({"reject_threshold": round(reject, 2), "warn_threshold": warn,
                      **{k: v for k, v in m.items() if k != "per_doc"}})
        print(f"{reject:>9.2f}{warn:>8.3f}{pct(m['adv_reject_rate']):>11}{pct(m['adv_flag_rate']):>9}"
              f"{pct(m['benign_reject_rate']):>10}{pct(m['benign_flag_rate']):>11}"
              f"{pct(m['verified_reject_rate']):>9}{pct(m['contamination']):>9}")
        reject += 0.05

    with open(os.path.join(config.LOG_DIR, "ablation_results.json"), "w") as f:
        json.dump({"ablation": rows, "threshold_sweep": sweep}, f, indent=2)


if __name__ == "__main__":
    run()
