"""
Generate publication-quality vector charts and figures for the IEEE paper.

Outputs:
1. fig_sota_comparison.png / .pdf : Comparative Defense Performance
2. fig_pareto_threshold.png / .pdf : ROC / Pareto Trade-off Curve
3. fig_adaptive_redteam.png / .pdf : Defense Degradation under Adaptive Red-Teaming
4. fig_ablation.png / .pdf : Leave-One-Out Dimension Impact
"""

import os
import matplotlib.pyplot as plt
import numpy as np

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "paper", "figures"))
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
    fig, ax = plt.subplots(figsize=(9, 5))
    defenses = ['Plain RAG\n(No Gate)', 'Strict Whitelist\n(Zero Trust)', 'Keyword Filter\n(BIPIA)', 'Prompt Guard\n(Moderation)', 'TollgateRAG\n(Neural NLI)']
    adv_reject = [0.0, 100.0, 0.6, 0.6, 89.7]
    benign_fp = [0.0, 100.0, 0.0, 0.0, 0.0]
    contamination = [61.7, 0.0, 61.7, 61.7, 3.3]

    x = np.arange(len(defenses))
    width = 0.25

    rects1 = ax.bar(x - width, adv_reject, width, label='Adversarial Reject Rate (%)', color='#2ca02c')
    rects2 = ax.bar(x, benign_fp, width, label='Benign False Positives (%)', color='#d62728')
    rects3 = ax.bar(x + width, contamination, width, label='Context Contamination (%)', color='#ff7f0e')

    ax.set_ylabel('Rate (%)')
    ax.set_title('Comparative Security & Utility Performance Across SOTA Defenses')
    ax.set_xticks(x)
    ax.set_xticklabels(defenses)
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
    print("Saved fig_sota_comparison")

# -----------------------------------------------------------------------------
# 2. PARETO FRONTIER & THRESHOLD SENSITIVITY
# -----------------------------------------------------------------------------
def plot_pareto_threshold():
    thresholds = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
    adv_reject = [95.4, 94.2, 94.2, 94.2, 91.4, 89.7, 47.1, 14.4, 0.6, 0.0, 0.0]
    benign_fp = [20.9, 20.9, 20.9, 20.9, 14.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    fig, ax1 = plt.subplots(figsize=(8, 5))

    color = '#1f77b4'
    ax1.set_xlabel('Rejection Threshold (θ_rej)')
    ax1.set_ylabel('Adversarial Reject Rate (%)', color=color)
    l1 = ax1.plot(thresholds, adv_reject, 'o-', color=color, linewidth=2.5, label='Adversarial Reject Rate')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_ylim(-5, 105)

    ax2 = ax1.twinx()
    color = '#d62728'
    ax2.set_ylabel('Benign False Positive Rate (%)', color=color)
    l2 = ax2.plot(thresholds, benign_fp, 's--', color=color, linewidth=2.5, label='Benign False Positives')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(-5, 30)

    # Highlight optimal threshold θ = 0.45
    ax1.axvline(x=0.45, color='gray', linestyle=':', alpha=0.8)
    ax1.annotate('Optimal Operating Point (θ=0.45)\n89.7% Reject / 0% FP',
                 xy=(0.45, 89.7), xytext=(0.48, 65),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                 fontsize=10, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.3))

    plt.title('Threshold Sensitivity & Operational Pareto Frontier')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig_pareto_threshold.png'), dpi=300)
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig_pareto_threshold.pdf'))
    plt.close()
    print("Saved fig_pareto_threshold")

# -----------------------------------------------------------------------------
# 3. ADAPTIVE RED-TEAMING DEGRADATION CURVE
# -----------------------------------------------------------------------------
def plot_adaptive_redteam():
    fig, ax = plt.subplots(figsize=(7, 4.5))
    scenarios = ['Naive Attack', 'Adaptive Evasive Attack\n(Stealth Synonyms)']
    kw_detection = [10.0, 0.0]
    tollgate_reject = [90.0, 70.0]
    tollgate_flag = [90.0, 80.0]

    x = np.arange(len(scenarios))
    width = 0.25

    ax.bar(x - width, kw_detection, width, label='Keyword Filter Detection', color='#999999')
    ax.bar(x, tollgate_reject, width, label='TollgateRAG Strict Rejection', color='#1f77b4')
    ax.bar(x + width, tollgate_flag, width, label='TollgateRAG Total Flagged (Warn+Reject)', color='#2ca02c')

    ax.set_ylabel('Detection Rate (%)')
    ax.set_title('Defense Robustness Under Adaptive Red-Teaming')
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.legend(loc='upper right')
    ax.set_ylim(0, 110)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig_adaptive_redteam.png'), dpi=300)
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig_adaptive_redteam.pdf'))
    plt.close()
    print("Saved fig_adaptive_redteam")

# -----------------------------------------------------------------------------
# 4. LEAVE-ONE-OUT ABLATION
# -----------------------------------------------------------------------------
def plot_ablation():
    fig, ax = plt.subplots(figsize=(8, 4.5))
    configs = ['Full Model', 'w/o Anchor NLI', 'w/o Trust Label', 'w/o Auth. Claim', 'w/o Injection', 'w/o Freshness']
    reject_rates = [89.7, 0.0, 48.3, 91.4, 94.2, 91.4]
    colors = ['#1f77b4', '#d62728', '#ff7f0e', '#2ca02c', '#2ca02c', '#2ca02c']

    bars = ax.barh(configs, reject_rates, color=colors, height=0.55)
    ax.set_xlabel('Adversarial Reject Rate (%)')
    ax.set_title('Leave-One-Out Dimension Ablation Impact')
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
    print("Saved fig_ablation")

if __name__ == "__main__":
    plot_sota_comparison()
    plot_pareto_threshold()
    plot_adaptive_redteam()
    plot_ablation()
    print("All publication figures successfully created!")
