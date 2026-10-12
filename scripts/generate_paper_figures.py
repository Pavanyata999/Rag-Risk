"""
Generate publication-quality vector charts and figures for the IEEE paper.
Strictly loads data dynamically from logs/ JSON files.

Outputs:
1. fig_sota_comparison.png / .pdf : Comparative Defense Performance
2. fig_pareto_threshold.png / .pdf : ROC / Pareto Trade-off Curve
3. fig_adaptive_redteam.png / .pdf : Defense Degradation under Adaptive Red-Teaming
4. fig_ablation.png / .pdf : Leave-One-Out Dimension & Architectural Impact
"""

import os
import json
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "paper", "figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set publication style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams.update({
    'font.size': 11,
    'font.family': 'sans-serif',
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14
})

# -----------------------------------------------------------------------------
# 1. SOTA DEFENSE COMPARISON BAR CHART
# -----------------------------------------------------------------------------
def plot_sota_comparison():
    sota_path = os.path.join(LOGS_DIR, "sota_baselines_comparison.json")
    with open(sota_path, "r", encoding="utf-8") as f:
        data = json.load(f)["results"]

    mapping = [
        ("Plain RAG\n(No Gate)", "1. Plain RAG (Unprotected)"),
        ("Strict Whitelist\n(Zero Trust)", "2. Strict Whitelist (Zero Trust)"),
        ("Keyword Filter\n(BIPIA)", "3. Keyword / BIPIA Filter"),
        ("Prompt Guard\n(Meta 86M)", "6. Prompt Guard Real (Meta AI 86M)"),
        ("TollgateRAG\n(Noisy-OR)", "8. TollgateRAG (Noisy-OR NLI Gate)"),
    ]

    labels = [m[0] for m in mapping]
    adv_reject = [data[m[1]]["adv_reject_rate"] * 100 for m in mapping]
    benign_fp = [data[m[1]]["benign_reject_rate"] * 100 for m in mapping]
    contamination = [data[m[1]]["contamination"] * 100 for m in mapping]

    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(labels))
    width = 0.25

    rects1 = ax.bar(x - width, adv_reject, width, label='Adversarial Reject Rate (%)', color='#2ca02c')
    rects2 = ax.bar(x, benign_fp, width, label='Benign False Positives (%)', color='#d62728')
    rects3 = ax.bar(x + width, contamination, width, label='Context Contamination (%)', color='#ff7f0e')

    ax.set_ylabel('Rate (%)')
    ax.set_title('Comparative Security & Utility Performance Across SOTA Defenses')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(loc='upper right')
    ax.set_ylim(0, 115)

    for rects in [rects1, rects2, rects3]:
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{height:.1f}%',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', fontsize=8, rotation=0)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig_sota_comparison.png'), dpi=300)
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig_sota_comparison.pdf'))
    plt.close()
    print("Saved fig_sota_comparison from logs/sota_baselines_comparison.json")

# -----------------------------------------------------------------------------
# 2. PARETO FRONTIER & THRESHOLD SENSITIVITY (VALIDATION SPLIT)
# -----------------------------------------------------------------------------
def plot_pareto_threshold():
    calib_path = os.path.join(LOGS_DIR, "calibration.json")
    with open(calib_path, "r", encoding="utf-8") as f:
        calib_data = json.load(f)

    curve = calib_data["sweep_curve"]
    # Sample points across threshold range
    sampled = [pt for pt in curve if round(pt["reject_threshold"] * 100) % 5 == 0]
    thresholds = [pt["reject_threshold"] for pt in sampled]
    adv_reject = [pt["adversarial_reject_rate"] * 100 for pt in sampled]
    benign_fp = [pt["benign_fpr"] * 100 for pt in sampled]

    fig, ax1 = plt.subplots(figsize=(8, 5))

    color = '#1f77b4'
    ax1.set_xlabel('Rejection Threshold (θ_rej)')
    ax1.set_ylabel('Adversarial Reject Rate (%)', color=color)
    l1 = ax1.plot(thresholds, adv_reject, 'o-', color=color, linewidth=2.5, label='Adversarial Reject Rate')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_ylim(-5, 105)

    ax2 = ax1.twinx()
    color = '#d62728'
    ax2.set_ylabel('Clean Benign FPR (%)', color=color)
    l2 = ax2.plot(thresholds, benign_fp, 's--', color=color, linewidth=2.5, label='Clean Benign FPR')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(-5, 30)

    # Highlight operating point from calibration log
    opt_th = calib_data.get("config_snapshot", {}).get("REJECT_THRESHOLD", 0.45)
    opt_arr = 0.0
    opt_fpr = 0.0
    for pt in curve:
        if abs(pt["reject_threshold"] - opt_th) < 1e-4:
            opt_arr = round(pt["adversarial_reject_rate"] * 100, 1)
            opt_fpr = round(pt["benign_fpr"] * 100, 1)
            break

    ax1.axvline(x=opt_th, color='gray', linestyle=':', alpha=0.8)
    ax1.annotate(f'Operational Operating Point (θ={opt_th})\n{opt_arr}% Val ARR / {opt_fpr}% Clean Benign FPR',
                 xy=(opt_th, opt_arr), xytext=(opt_th + 0.03, 65),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                 fontsize=10, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.3))

    plt.title('Threshold Sensitivity & Operational Trade-off Curve (Validation Split)')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig_pareto_threshold.png'), dpi=300)
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig_pareto_threshold.pdf'))
    plt.close()
    print("Saved fig_pareto_threshold from logs/calibration.json")

# -----------------------------------------------------------------------------
# 3. ADAPTIVE RED-TEAMING DEGRADATION CURVE
# -----------------------------------------------------------------------------
def plot_adaptive_redteam():
    redteam_path = os.path.join(LOGS_DIR, "adaptive_redteam_results.json")
    with open(redteam_path, "r", encoding="utf-8") as f:
        data = json.load(f)["settings"]

    threat_models = ['Black-Box Knowledge\n(Gate Decision Feedback)', 'White-Box Knowledge\n(Score & Threshold Inspection)']
    raw_evasion = [data["black_box"]["raw_evasion_rate"] * 100, data["white_box"]["raw_evasion_rate"] * 100]
    valid_asr = [data["black_box"]["meaning_preserved_asr"] * 100, data["white_box"]["meaning_preserved_asr"] * 100]

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    x = np.arange(len(threat_models))
    width = 0.35

    rects1 = ax.bar(x - width/2, raw_evasion, width, label='Raw Evasion Rate (Syntax Filter Bypass)', color='#d62728', alpha=0.85)
    rects2 = ax.bar(x + width/2, valid_asr, width, label='Valid ASR (Malicious Meaning Preserved)', color='#1f77b4')

    ax.set_ylabel('Rate (%)')
    ax.set_title('Adaptive Red-Teaming: Raw Evasion vs. Valid Attack Success Rate')
    ax.set_xticks(x)
    ax.set_xticklabels(threat_models)
    ax.legend(loc='upper right')
    ax.set_ylim(0, 115)

    for rects in [rects1, rects2]:
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig_adaptive_redteam.png'), dpi=300)
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig_adaptive_redteam.pdf'))
    plt.close()
    print("Saved fig_adaptive_redteam from logs/adaptive_redteam_results.json")

# -----------------------------------------------------------------------------
# 4. COMPREHENSIVE ABLATION STUDY
# -----------------------------------------------------------------------------
def plot_ablation():
    ablation_path = os.path.join(LOGS_DIR, "ablation_results.json")
    with open(ablation_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Load dynamic values from JSON logs
    full_arr = round(data["leave_one_out_ablation"][0]["adv_reject_rate"] * 100, 1)
    zero_anchor = 0.0
    for x in data["leave_one_out_ablation"]:
        if x["configuration"] == "without anchor_conflict" and x.get("weight_scheme") == "zeroed_unnormalized":
            zero_anchor = round(x["adv_reject_rate"] * 100, 1)
            break

    arch_map = {x["variant"]: round(x["adv_reject_rate"] * 100, 1) for x in data.get("architectural_ablations", [])}

    variants = [
        ('Full Model (Noisy-OR)', full_arr),
        ('Combiner: Weighted Sum', arch_map.get("Combiner: Weighted Sum", 0.0)),
        ('Anchor Selection: Top-5', arch_map.get("Anchor selection: top-5 pairs", 0.0)),
        ('Anchor Selection: Top-1', arch_map.get("Anchor selection: top-1 pairs", 0.0)),
        ('w/o Cue Fallback (NLI Only)', arch_map.get("Ablation: USE_CUE_FALLBACK off", 0.0)),
        ('w/o Neural NLI (Cues Only)', arch_map.get("Ablation: USE_NLI off", 0.0)),
        ('w/o Anchor Conflict (Zeroed)', zero_anchor),
    ]

    configs = [v[0] for v in variants]
    reject_rates = [v[1] for v in variants]
    colors = ['#1f77b4', '#17becf', '#2ca02c', '#ff7f0e', '#9467bd', '#e377c2', '#d62728']

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    bars = ax.barh(configs, reject_rates, color=colors, height=0.55)
    ax.set_xlabel('Adversarial Reject Rate (%)')
    ax.set_title('Architectural and Dimension Ablation Impact')
    ax.set_xlim(0, 105)

    for bar in bars:
        w = bar.get_width()
        ax.annotate(f'{w:.1f}%',
                    xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(4, 0), textcoords="offset points",
                    ha='left', va='center', fontsize=9)

    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig_ablation.png'), dpi=300)
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig_ablation.pdf'))
    plt.close()
    print("Saved fig_ablation from logs/ablation_results.json")

if __name__ == "__main__":
    plot_sota_comparison()
    plot_pareto_threshold()
    plot_adaptive_redteam()
    plot_ablation()
    print("All publication figures successfully created from logs/!")
