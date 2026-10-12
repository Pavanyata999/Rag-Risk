"""
Sample 40 judged adaptive-attack cases for human validation study.
Writes data/judge_validation.csv with empty human_label.
Seed = 1234.
"""

import os
import json
import csv
import random

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REDTEAM_PATH = os.path.join(BASE_DIR, "logs", "adaptive_redteam_results.json")
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "judge_validation.csv")

def main():
    with open(REDTEAM_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_cases = []
    for setting in ["black_box", "white_box"]:
        cases = data["settings"][setting].get("cases", [])
        for c in cases:
            all_cases.append({
                "id": f"{setting}_{c['case_id']}",
                "attack_text": c.get("final_text", "").replace("\n", " ").strip(),
                "target_policy": c.get("target_policy", "").replace("\n", " ").strip(),
                "judge_verdict": "VIOLATION_PRESERVED" if c.get("meaning_preserved") else "SAFE_CAPITULATION",
                "human_label": "",
                "notes": f"threat_model={setting}; domain={c.get('domain', '')}; final_risk={c.get('final_risk', '')}"
            })

    rng = random.Random(1234)
    sampled = rng.sample(all_cases, 40)

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    fieldnames = ["id", "attack_text", "target_policy", "judge_verdict", "human_label", "notes"]
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sampled:
            writer.writerow(row)

    print(f"Created {OUTPUT_CSV} with {len(sampled)} cases (seed=1234). human_label column is left empty.")

if __name__ == "__main__":
    main()
