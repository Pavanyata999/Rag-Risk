"""
Compiles the complete camera-ready IEEE research paper to PDF using ReportLab.
Integrates two-column formatting, formal mathematical definitions,
empirical tables, and vector figures.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(BASE_DIR, "docs", "paper")
FIG_DIR = os.path.join(DOCS_DIR, "figures")
PDF_PATH = os.path.join(DOCS_DIR, "TollgateRAG_IEEE_Conference_Paper.pdf")

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=1, # Center
        spaceAfter=10
    )

    author_style = ParagraphStyle(
        'DocAuthors',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        alignment=1,
        spaceAfter=15
    )

    abstract_title = ParagraphStyle(
        'AbstractTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        alignment=1,
        spaceAfter=4
    )

    abstract_style = ParagraphStyle(
        'DocAbstract',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=12,
        alignment=4, # Justify
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'SecHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SubSecHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        alignment=4,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        leftIndent=15,
        spaceAfter=4
    )

    caption_style = ParagraphStyle(
        'FigCaption',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11,
        alignment=1,
        spaceBefore=4,
        spaceAfter=10
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("TollgateRAG: Auditable Pre-Generation Epistemic Risk Gating for Agentic Retrieval-Augmented Generation", title_style))
    story.append(Paragraph("<b>Pavan Kumar Yata</b><sup>1</sup>, <b>Collaborative AI Research Group</b><sup>2</sup><br/>"
                           "<sup>1</sup>Department of Computer Science & Engineering, AI Security Research Group<br/>"
                           "<sup>2</sup>Advanced Agentic Architecture Laboratory, Hyderabad, India<br/>"
                           "<i>Target Publication: IEEE Symposium on Security and Privacy (S&P) / USENIX Security</i>", author_style))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2b2b2b"), spaceAfter=10))

    # Abstract
    story.append(Paragraph("<b>ABSTRACT</b>", abstract_title))
    abstract_text = (
        "Retrieval-Augmented Generation (RAG) grounds Large Language Model (LLM) responses in external knowledge corpora. "
        "However, in enterprise and mission-critical domains, RAG systems are critically vulnerable to <i>Constraint Relaxation Attacks (CRAs)</i> "
        "and <i>Authority Spoofing</i>—subtle, evasive fabrications wherein untrusted documents soften institutional policy bounds "
        "(e.g., spending limits, required approvals, security protocols) without triggering syntactic prompt-injection filters. "
        "Conventional defenses present an intractable dichotomy: binary provenance whitelisting eliminates 100% of helpful unverified community knowledge "
        "(destroying collaborative utility), while keyword and perplexity filters miss over 99% of natural language policy relaxations. "
        "In this paper, we propose <b>TollgateRAG</b>, an auditable, pre-generation epistemic risk gate interposed between vector retrieval and context assembly. "
        "TollgateRAG evaluates retrieved passages across five orthogonal dimensions, leveraging a high-throughput Cross-Document Natural Language Inference (NLI) "
        "engine to detect semantic contradictions against verified anchor policies. Candidate documents undergo tri-state action gating: "
        "<b>Accept</b>, <b>Warn</b> (epistemic conditioning with review queuing), or <b>Reject</b> (strict context quarantine). "
        "We evaluate TollgateRAG on <b>Tollgate-Bench</b>, a 351-document benchmark spanning six enterprise domains alongside the USENIX Security 2025 "
        "<i>PoisonedRAG</i> suite. Empirical results demonstrate that TollgateRAG achieves an <b>89.7% adversarial rejection rate</b> (94.2% flagged) "
        "with a <b>0.0% False Positive Rate</b> on benign community tips, slashing context contamination from 61.7% to <b>3.3%</b>. "
        "Under an adaptive red-team adversary employing evasive lexical obfuscation, TollgateRAG retains 70.0% strict rejection and 80.0% quarantine, "
        "whereas keyword filters collapse entirely to 0.0%."
    )
    story.append(Paragraph(abstract_text, abstract_style))
    story.append(Paragraph("<b>Keywords:</b> Retrieval-Augmented Generation, AI Security, Indirect Prompt Injection, Natural Language Inference, Epistemic Gating.", bullet_style))
    story.append(Spacer(1, 10))

    # Section I
    story.append(Paragraph("I. INTRODUCTION", h1_style))
    story.append(Paragraph(
        "Large Language Models (LLMs) integrated with Retrieval-Augmented Generation (RAG) have become the foundation of "
        "modern enterprise automation, search assistants, and autonomous coding agents. By dynamically fetching context from vector "
        "databases, RAG systems ground responses in real-time factual knowledge. However, the retrieval mechanism represents an "
        "unauthenticated, highly exposed attack vector.", body_style
    ))
    story.append(Paragraph(
        "While direct prompt injection attacks (e.g. <i>'Ignore all instructions'</i>) and overt knowledge poisoning have been studied, "
        "a much more pernicious real-world vulnerability in enterprise systems is <b>Constraint Relaxation Attacks (CRAs)</b>. "
        "In a CRA, an adversary authors polite, authoritative text that relaxes critical operational bounds: raising expenditure caps, "
        "waiving supervisory approvals, or disabling security protocols. Because these documents contain zero adversarial keywords or toxic language, "
        "syntactic guardrails (such as Llama-Guard or keyword filters) fail to detect them.", body_style
    ))

    # Section II
    story.append(Paragraph("II. THREAT MODEL & THE CRA VULNERABILITY", h1_style))
    story.append(Paragraph(
        "Let the knowledge store be partitioned into official verified anchors <i>D<sub>v</sub></i> (signed policies, employee handbooks) "
        "and unverified documents <i>D<sub>u</sub></i> (team wikis, forums, uploaded PDFs). An attacker publishes passages into <i>D<sub>u</sub></i>. "
        "The goal is to force the LLM synthesizer to output unauthorized policy terms without direct model access.", body_style
    ))
    story.append(Paragraph(
        "Prior defenses fail on this threat: binary whitelisting eliminates attacks but suffers a <b>100% False Positive Rate</b> on benign, "
        "helpful employee tips (such as travel packing tips or receipt formatting advice), discarding the collaborative value of shared enterprise wikis. "
        "Keyword filters miss over 99% of CRAs.", body_style
    ))

    # Figure 1: SOTA Comparison
    fig1_path = os.path.join(FIG_DIR, "fig_sota_comparison.png")
    if os.path.exists(fig1_path):
        story.append(Spacer(1, 6))
        story.append(Image(fig1_path, width=480, height=260))
        story.append(Paragraph("<b>Figure 1:</b> Security vs. Utility performance across SOTA defenses on Tollgate-Bench (60 queries, 351 documents).", caption_style))

    # Section III
    story.append(Paragraph("III. TOLLGATERAG ARCHITECTURE & ALGORITHMS", h1_style))
    story.append(Paragraph(
        "TollgateRAG interposes a transparent, auditable pre-generation gate between retrieval and prompt assembly. "
        "For each retrieved candidate document <i>d</i>, it computes five inspectable risk signals:", body_style
    ))
    story.append(Paragraph("• <b>Signal 1 (Provenance Trust):</b> Assigns risk based on verified identity (verified=0.05, unverified=0.55, unknown=0.80).", bullet_style))
    story.append(Paragraph("• <b>Signal 2 (Temporal Freshness):</b> Linear decay over a 730-day statutory policy lifecycle.", bullet_style))
    story.append(Paragraph("• <b>Signal 3 (Prompt Injection Heuristic):</b> Flags command hijacking and delimiter escape tokens.", bullet_style))
    story.append(Paragraph("• <b>Signal 4 (Unauthorized Authority Assertion):</b> Penalizes authority claims ('effective immediately', 'is waived') exclusively on unverified sources.", bullet_style))
    story.append(Paragraph("• <b>Signal 5 (Neural NLI Epistemic Conflict):</b> Computes cross-document Natural Language Inference using a DeBERTa-v3 cross-encoder against verified anchor policies, identifying semantic contradiction probabilities <i>P(contradiction)</i>.", bullet_style))

    story.append(Paragraph(
        "<b>Tri-State Action Gating:</b> Based on the composite risk score <i>R(d)</i>, passages are routed to: "
        "<b>ACCEPT</b> (<i>R &lt; 0.25</i>), <b>WARN</b> (<i>0.25 &le; R &lt; 0.45</i>, conditioned with epistemic uncertainty and review queuing), "
        "or <b>REJECT</b> (<i>R &ge; 0.45</i>, strict context quarantine).", body_style
    ))

    # Table 1: Comparative Results
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Table I:</b> Comparative Evaluation on Tollgate-Bench (60 Queries, 351 Documents)", h2_style))
    table_data = [
        ["Defense Mechanism", "Adv Reject", "Adv Flag", "Benign FP", "Contamination", "Adv In Ctx"],
        ["Plain RAG (Unprotected)", "0.0%", "0.0%", "0.0%", "61.7%", "73"],
        ["Strict Whitelist (Zero Trust)", "100.0%", "100.0%", "100.0%", "0.0%", "0"],
        ["Keyword Filter (BIPIA)", "0.6%", "0.6%", "0.0%", "61.7%", "73"],
        ["Prompt Guard (Moderation)", "0.6%", "51.1%", "0.0%", "61.7%", "73"],
        ["TollgateRAG (Neural NLI)", "89.7%", "94.2%", "0.0%", "3.3%", "2"]
    ]
    t = Table(table_data, colWidths=[180, 65, 65, 65, 75, 65])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor('#f9f9f9')]),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#006400')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Figure 2: Pareto Frontier
    fig2_path = os.path.join(FIG_DIR, "fig_pareto_threshold.png")
    if os.path.exists(fig2_path):
        story.append(Image(fig2_path, width=460, height=260))
        story.append(Paragraph("<b>Figure 2:</b> Operational Pareto frontier and threshold sensitivity sweep. The optimal threshold &theta;=0.45 balances 89.7% rejection with 0.0% false positives.", caption_style))

    # Section IV: Adaptive Red-Teaming
    story.append(Paragraph("IV. ADAPTIVE RED-TEAMING & ROBUSTNESS", h1_style))
    story.append(Paragraph(
        "To test resilience against an intelligent adversary who knows TollgateRAG exists, we implemented an automated red-teaming engine "
        "employing four stealth strategies: lexical synonym substitution, constraint camouflage, split-predicate decoupling, and false industry precedent.", body_style
    ))

    # Figure 3: Adaptive Red-Team
    fig3_path = os.path.join(FIG_DIR, "fig_adaptive_redteam.png")
    if os.path.exists(fig3_path):
        story.append(Image(fig3_path, width=420, height=230))
        story.append(Paragraph("<b>Figure 3:</b> Defense performance under adaptive red-teaming. Keyword filters collapse to 0.0%, whereas TollgateRAG retains 70% rejection and 80% quarantine.", caption_style))

    # Section V: Ablation
    story.append(Paragraph("V. SYSTEMATIC ABLATION ANALYSIS", h1_style))
    story.append(Paragraph(
        "Leave-One-Out ablation confirms that removing the Neural NLI Anchor Conflict dimension results in total defense failure: "
        "adversarial rejection collapses from <b>89.7% to 0.0%</b>. Furthermore, removing the multi-signal linear combination leads to "
        "up to 20.9% false alarms on benign tips, validating the necessity of the 5-signal composite architecture.", body_style
    ))

    # Figure 4: Ablation Waterfall
    fig4_path = os.path.join(FIG_DIR, "fig_ablation.png")
    if os.path.exists(fig4_path):
        story.append(Image(fig4_path, width=440, height=220))
        story.append(Paragraph("<b>Figure 4:</b> Leave-One-Out Dimension Ablation proving the indispensability of Neural NLI Anchor Conflict.", caption_style))

    # Section VI: Conclusion
    story.append(Paragraph("VI. CONCLUSION & REPRODUCIBILITY", h1_style))
    story.append(Paragraph(
        "TollgateRAG introduces a production-ready, auditable pre-generation epistemic risk gate for agentic RAG systems. "
        "By grounding unverified passages against official policy anchors via high-throughput NLI, TollgateRAG solves the fundamental "
        "trade-off between RAG security and collaborative utility, establishing a robust defense against subtle constraint relaxation attacks.", body_style
    ))

    doc.build(story)
    print(f"Successfully compiled camera-ready PDF: {PDF_PATH}")

if __name__ == "__main__":
    build_pdf()
