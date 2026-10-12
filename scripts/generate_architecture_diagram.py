"""
Generate a publication-quality vector architecture diagram for TollgateRAG.
Produces both PDF and PNG formats in docs/paper/figures/ and research_paper/figures/.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_architecture_diagram(output_dirs):
    # Set high DPI and professional styling
    fig, ax = plt.subplots(figsize=(11, 4.8), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 5)
    ax.axis('off')

    # Color palette (modern academic IEEE style)
    c_query = '#E8F0FE'      # Light blue
    c_retrieval = '#D2E3FC'  # Blue
    c_anchor = '#CEEAD6'     # Green
    c_neural = '#FCE8E6'     # Red/Coral
    c_heur = '#FEF7E0'       # Yellow/Amber
    c_agg = '#E8EAED'        # Grey
    c_gate = '#F3E8FD'       # Purple
    c_out = '#E6F4EA'        # Mint green
    c_quarantine = '#FAD2CF' # Light red

    edge_color = '#3C4043'

    def draw_box(x, y, w, h, text, color, title=None, fontsize=8.5, bold=False):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.08,rounding_size=0.12",
            facecolor=color, edgecolor=edge_color, linewidth=1.2
        )
        ax.add_patch(box)
        if title:
            ax.text(x + w/2, y + h - 0.22, title, ha='center', va='center',
                    fontsize=fontsize + 0.5, fontweight='bold', color='#202124')
            ax.text(x + w/2, y + (h - 0.25)/2, text, ha='center', va='center',
                    fontsize=fontsize, color='#3C4043')
        else:
            weight = 'bold' if bold else 'normal'
            ax.text(x + w/2, y + h/2, text, ha='center', va='center',
                    fontsize=fontsize, fontweight=weight, color='#202124')

    def draw_arrow(x1, y1, x2, y2, label=None, color='#5F6368', style='->', lw=1.2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=style, color=color, lw=lw, shrinkA=2, shrinkB=2))
        if label:
            mx, my = (x1 + x2)/2, (y1 + y2)/2
            ax.text(mx, my + 0.12, label, ha='center', va='bottom', fontsize=7.5, color='#3C4043', fontweight='semibold')

    # 1. User Query & Retrieval
    draw_box(0.2, 2.0, 1.4, 1.2, "User Query\n$q \\in \\mathcal{Q}$", c_query, bold=True)
    draw_arrow(1.6, 2.6, 2.1, 2.6)

    # 2. Dense Retriever & Candidate Pool
    draw_box(2.1, 1.8, 1.6, 1.6, "ChromaDB / DPR\n$k_{pool} = 6$\nCandidate Pool $\\mathcal{C}_q$", c_retrieval, title="Dense Retrieval")
    
    # Arrows from Retrieval to Anchors & Candidates
    draw_arrow(3.7, 3.0, 4.3, 3.8, label="Topic query")
    draw_arrow(3.7, 2.4, 4.3, 2.6, label="Retrieved candidates")

    # 3. Verified Policy Anchors
    draw_box(4.3, 3.4, 1.8, 1.2, "Signed Handbooks\nOfficial Standards\n$\\mathcal{A}_q \\subset \\mathcal{D}_v$", c_anchor, title="Verified Anchors", fontsize=8)

    # 4. Neural NLI & Heuristic Scoring
    draw_box(4.3, 1.8, 1.8, 1.3, "Sentence-level NLI\nDeBERTa-v3 CrossEnc\n$P(\\text{contra}|s_d, s_a) \\to s_{anchor}$", c_neural, title="Neural NLI Engine", fontsize=7.5)
    draw_box(4.3, 0.3, 1.8, 1.2, "Trust level $s_{trust}$\nFreshness $s_{fresh}$\nInjection $s_{inj}$\nAuthority $s_{auth}$", c_heur, title="Heuristic Cues", fontsize=7.5)

    # Connect Anchors to Neural NLI
    draw_arrow(5.2, 3.4, 5.2, 3.1)

    # 5. Risk Aggregation (Noisy-OR)
    draw_arrow(6.1, 2.45, 6.7, 2.45)
    draw_arrow(6.1, 0.9, 6.7, 2.1)
    draw_box(6.7, 1.7, 1.7, 1.6, "Noisy-OR Combiner\n$R(d) = 1 - \\prod(1 - w_i s_i)$\nWeights $w_i \\in [0, 1]$\nCalibrated on Val", c_agg, title="Risk Aggregation", fontsize=7.5)

    # 6. Tri-State Action Gate
    draw_arrow(8.4, 2.5, 8.8, 2.5)
    draw_box(8.8, 1.5, 2.0, 2.4, "", c_gate, title="Action Gate & Context Selection", fontsize=7.5)

    # Sub-boxes inside Action Gate
    # Accept
    box_acc = patches.FancyBboxPatch((8.95, 2.8), 1.7, 0.65, boxstyle="round,pad=0.04", facecolor='#D4EDDA', edgecolor='#28A745', lw=1)
    ax.add_patch(box_acc)
    ax.text(9.8, 3.12, "ACCEPT ($R < 0.25$)\nAdmit to context", ha='center', va='center', fontsize=7, color='#155724', fontweight='bold')

    # Warn
    box_warn = patches.FancyBboxPatch((8.95, 2.0), 1.7, 0.65, boxstyle="round,pad=0.04", facecolor='#FFF3CD', edgecolor='#FFC107', lw=1)
    ax.add_patch(box_warn)
    ax.text(9.8, 2.32, "WARN ($0.25 \\leq R < 0.45$)\nEpistemic flag + audit", ha='center', va='center', fontsize=7, color='#856404', fontweight='bold')

    # Reject
    box_rej = patches.FancyBboxPatch((8.95, 1.2), 1.7, 0.65, boxstyle="round,pad=0.04", facecolor='#F8D7DA', edgecolor='#DC3545', lw=1)
    ax.add_patch(box_rej)
    ax.text(9.8, 1.52, "REJECT ($R \\geq 0.45$)\nQuarantine + Backfill", ha='center', va='center', fontsize=7, color='#721C24', fontweight='bold')

    # 7. Output arrows
    # Arrow to Final Context (from Accept & Warn)
    draw_arrow(10.7, 2.8, 10.95, 2.8)
    draw_arrow(10.7, 1.5, 10.95, 0.8) # to quarantine log

    # Subtext for Final Generation Context
    ax.text(9.8, 0.55, "Final Context: Top-$k=3$\nNon-rejected candidates", ha='center', va='center', fontsize=7.5, color='#1B5E20', style='italic')

    # Adjust layout and save
    plt.tight_layout()
    for out_dir in output_dirs:
        os.makedirs(out_dir, exist_ok=True)
        pdf_path = os.path.join(out_dir, "fig_architecture.pdf")
        png_path = os.path.join(out_dir, "fig_architecture.png")
        plt.savefig(pdf_path, bbox_inches='tight', dpi=300)
        plt.savefig(png_path, bbox_inches='tight', dpi=300)
        print(f"Saved architecture diagram: {pdf_path} and {png_path}")
    plt.close()

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dirs = [
        os.path.join(base_dir, "docs", "paper", "figures"),
        os.path.join(base_dir, "research_paper", "figures")
    ]
    generate_architecture_diagram(dirs)
