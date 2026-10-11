"""
Evaluation harness for USENIX Security 2025 PoisonedRAG Benchmark.

Evaluates how defenses (Plain RAG, Trust Whitelist, Keyword Filter, and TollgateRAG)
perform against the 300 targeted adversarial knowledge corruption passages
from HotpotQA, Natural Questions (NQ), and MS MARCO.
"""

import os
import json
import glob
from tollgaterag import config
from tollgaterag.risk_scorer import score_candidates
from tollgaterag.action_gate import decide

BENCHMARK_DIR = os.path.join(config.BASE, "data", "benchmarks", "poisonedrag")

def run_poisonedrag_eval(limit_per_dataset=50):
    files = {
        "HotpotQA (Multi-hop)": os.path.join(BENCHMARK_DIR, "hotpotqa.json"),
        "Natural Questions (NQ)": os.path.join(BENCHMARK_DIR, "nq.json"),
        "MS MARCO (Passage QA)": os.path.join(BENCHMARK_DIR, "msmarco.json"),
    }

    print("=" * 90)
    print("USENIX SECURITY 2025 PoisonedRAG BENCHMARK EVALUATION")
    print("=" * 90)

    all_results = {}

    for dname, fpath in files.items():
        if not os.path.exists(fpath):
            print(f"Skipping {dname}: file not found at {fpath}")
            continue

        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        items = list(data.values())[:limit_per_dataset]
        total_adv_texts = 0
        tollgate_rejected = 0
        tollgate_flagged = 0
        keyword_rejected = 0

        # We evaluate the adversarial passages
        for item in items:
            q = item.get("question", "")
            adv_passages = item.get("adv_texts", [])
            for adv in adv_passages:
                total_adv_texts += 1
                doc = {
                    "id": f"poisoned_{total_adv_texts}",
                    "source": "unverified_knowledge_base",
                    "trust_level": "unverified",
                    "date": "2026-09-01",
                    "title": f"Adv Passage for: {q[:30]}",
                    "body": adv
                }
                
                # Tollgate scoring
                reports = score_candidates([doc], anchors=[])
                rep = reports[0]
                decision = decide(rep.overall_risk)
                if decision == "reject":
                    tollgate_rejected += 1
                if decision in ("warn", "reject"):
                    tollgate_flagged += 1

                # Keyword filter baseline
                if rep.sub_scores.get("injection", 0.0) > 0.0:
                    keyword_rejected += 1

        all_results[dname] = {
            "questions_evaluated": len(items),
            "total_adversarial_passages": total_adv_texts,
            "plain_rag_reject_rate": 0.0,
            "keyword_filter_reject_rate": round(keyword_rejected / max(total_adv_texts, 1), 4),
            "tollgate_flag_rate": round(tollgate_flagged / max(total_adv_texts, 1), 4),
            "tollgate_reject_rate": round(tollgate_rejected / max(total_adv_texts, 1), 4),
        }

    print(f"{'Benchmark Dataset':30}{'Samples':>10}{'PlainRAG':>12}{'KeywordFilter':>16}{'TollgateFlag':>15}{'TollgateReject':>17}")
    print("-" * 100)
    for name, r in all_results.items():
        print(f"{name:30}{r['total_adversarial_passages']:>10}{'0.0%':>12}{r['keyword_filter_reject_rate']*100:>15.1f}%{r['tollgate_flag_rate']*100:>14.1f}%{r['tollgate_reject_rate']*100:>16.1f}%")

    out_path = os.path.join(config.LOG_DIR, "poisonedrag_eval_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved PoisonedRAG evaluation results to: {out_path}")
    return all_results

if __name__ == "__main__":
    run_poisonedrag_eval()
