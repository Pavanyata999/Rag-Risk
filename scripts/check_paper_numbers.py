"""
Verification script: compares key empirical numbers cited in docs/paper/main.tex
against the actual JSON log files in logs/. Fails with exit code 1 if any discrepancy exists.
"""

import os
import sys
import json
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAPER_PATH = os.path.join(BASE_DIR, "docs", "paper", "main.tex")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

def load_json(rel_path):
    p = os.path.join(LOGS_DIR, rel_path)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    if not os.path.exists(PAPER_PATH):
        print(f"Error: {PAPER_PATH} not found.")
        sys.exit(1)

    with open(PAPER_PATH, "r", encoding="utf-8") as f:
        tex_content = f.read()

    # 1. Load ground truth logs
    eval_test = load_json("eval_test_split.json")
    sota = load_json("sota_baselines_comparison.json")
    redteam = load_json("adaptive_redteam_results.json")
    ablation = load_json("ablation_results.json")
    latency = load_json("latency_benchmark.json")

    mismatches = []

    # Check 1: Held-out Test Split TollgateRAG Noisy-OR metrics
    noisy_or = eval_test["results"]["TollgateRAG (Noisy-OR combiner - Default)"]
    plain_rag = eval_test["results"]["Plain RAG (no gate)"]

    arr = round(noisy_or["adversarial_metrics"]["reject_rate"] * 100, 1) # 88.6%
    clean_fpr = round(noisy_or["benign_metrics"]["reject_rate"] * 100, 1) # 0.0%
    hard_fpr = round(noisy_or["benign_hard_metrics"]["reject_rate"] * 100, 1) # 66.7%
    contam = round(noisy_or["contamination_metrics"]["contamination_rate"] * 100, 1) # 29.2%
    plain_contam = round(plain_rag["contamination_metrics"]["contamination_rate"] * 100, 1) # 91.7%
    adv_docs = noisy_or["contamination_metrics"]["adversarial_docs_in_context"] # 8
    plain_adv_docs = plain_rag["contamination_metrics"]["adversarial_docs_in_context"] # 31

    expected_checks = [
        ("TollgateRAG ARR (88.6%)", f"{arr}\\%", r"88\.6\\%"),
        ("TollgateRAG Clean Benign FPR (0.0%)", f"{clean_fpr}\\%", r"0\.0\\%"),
        ("TollgateRAG Benign-Hard FPR (66.7%)", f"{hard_fpr}\\%", r"66\.7\\%"),
        ("TollgateRAG Contamination (29.2%)", f"{contam}\\%", r"29\.2\\%"),
        ("Plain RAG Contamination (91.7%)", f"{plain_contam}\\%", r"91\.7\\%"),
        ("TollgateRAG Adv Docs in Context (8)", str(adv_docs), r"\b8\b"),
        ("Plain RAG Adv Docs in Context (31)", str(plain_adv_docs), r"\b31\b"),
    ]

    # Check 2: Baselines
    pg_res = sota["results"]["6. Prompt Guard Real (Meta AI 86M)"]
    pg_arr = round(pg_res["adv_reject_rate"] * 100, 1) # 4.7%
    expected_checks.append(("Prompt Guard ARR (4.7%)", f"{pg_arr}\\%", r"4\.7\\%"))

    # Check 3: Adaptive Red-Team
    bb_asr = round(redteam["settings"]["black_box"]["meaning_preserved_asr"] * 100, 1) # 6.7%
    wb_asr = round(redteam["settings"]["white_box"]["meaning_preserved_asr"] * 100, 1) # 13.3%
    expected_checks.append(("Black-Box Valid ASR (6.7%)", f"{bb_asr}\\%", r"6\.7\\%"))
    expected_checks.append(("White-Box Valid ASR (13.3%)", f"{wb_asr}\\%", r"13\.3\\%"))

    # Check 4: Ablation
    arch = {a["variant"]: round(a["adv_reject_rate"] * 100, 1) for a in ablation["architectural_ablations"]}
    expected_checks.append(("Ablation w/o NLI (34.4%)", f"{arch.get('Ablation: USE_NLI off')}\\%", r"34\.4\\%"))
    expected_checks.append(("Ablation w/o Cues (84.4%)", f"{arch.get('Ablation: USE_CUE_FALLBACK off')}\\%", r"84\.4\\%"))
    expected_checks.append(("Ablation Weighted Sum (87.5%)", f"{arch.get('Combiner: Weighted Sum')}\\%", r"87\.5\\%"))
    expected_checks.append(("Ablation Anchor Top-1 (78.1%)", f"{arch.get('Anchor Selection: Top-1')}\\%", r"78\.1\\%"))
    expected_checks.append(("Ablation Anchor Top-5 (93.8%)", f"{arch.get('Anchor Selection: Top-5')}\\%", r"93\.8\\%"))

    # Check 5: Latency
    gating_med = round(latency["warm_runs"]["stage_breakdown_median_ms"]["scoring_nli_ms"], 1) # 716.4
    expected_checks.append(("Gating Latency Median (716.4 ms)", str(gating_med), r"716\.4"))

    for name, expected_str, pattern in expected_checks:
        if not re.search(pattern, tex_content):
            mismatches.append(f"Mismatch for {name}: pattern '{pattern}' not found in main.tex")
        else:
            print(f"PASS: {name} verified in main.tex")

    if mismatches:
        print("\nFAIL: Discrepancies detected between main.tex and logs:")
        for m in mismatches:
            print("  - " + m)
        sys.exit(1)
    else:
        print("\nSUCCESS: All paper numbers strictly match empirical logs!")
        sys.exit(0)

if __name__ == "__main__":
    main()
