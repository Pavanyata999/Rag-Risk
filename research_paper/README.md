# TollgateRAG Research Manuscript Package

This directory contains the authoritative research paper sources, figures, tables, and compilation infrastructure for:

> **TollgateRAG: Auditable Pre-Generation Epistemic Risk Gating for Agentic Retrieval-Augmented Generation**  
> Formatted as a 6-page camera-ready IEEE conference manuscript (`IEEEtran`).

---

## Directory Organization

```
research_paper/
├── main.tex                 # Authoritative LaTeX manuscript source
├── main.pdf                 # Compiled 6-page IEEE camera-ready PDF
├── references.bib           # Verified BibTeX references (14 peer-reviewed entries)
├── results_macros.tex       # Auto-generated LaTeX macros from logs/*.json
├── claims_registry.json     # Machine-readable quantitative claims registry (21 claims)
├── figures/                 # Publication-ready vector PDF & high-res PNG figures
│   ├── fig_architecture.pdf # Fig. 1: Complete TollgateRAG system architecture
│   ├── fig_pareto_threshold.pdf # Fig. 2: Threshold sensitivity Pareto trade-off curve
│   ├── fig_adaptive_redteam.pdf # Fig. 3: Closed-loop adaptive red-teaming dynamics
│   ├── fig_sota_comparison.pdf  # Comparative SOTA benchmark visualization
│   └── fig_ablation.pdf     # Component ablation study visualization
├── figure_sources/          # Standalone Python scripts to regenerate all figures
│   ├── generate_architecture_diagram.py
│   └── generate_paper_figures.py
├── tables/                  # Generated LaTeX tables matching authoritative logs
│   ├── tab_sota.tex         # Table I: Comparative SOTA benchmark
│   ├── tab_attack_classes.tex # Table II: Attack subtype breakdown
│   ├── tab_ablation.tex     # Table III: Ablation study
│   ├── tab_latency_kpi.tex  # Table IV: Latency breakdown & KPI reconciliation
│   ├── tab_latency.tex      # Standalone latency profile table
│   └── tab_kpi.tex          # Standalone KPI reconciliation table
├── scripts/                 # Reproducibility and verification test suite
│   ├── check_paper_numbers.py # Automated claims validator against logs/*.json
│   ├── check_no_secrets.py  # Zero-secrets git history and repo scanner
│   ├── check_references.py  # 100% DOI/venue bibliographic validator
│   ├── make_result_macros.py # Script generating results_macros.tex and tables
│   └── reproduce.py         # End-to-end benchmark reproduction orchestrator
├── README.md                # This reproduction and directory guide
├── PAPER_CLAIMS.md          # Traceability matrix mapping claims to raw log evidence
└── SUBMISSION_CHECKLIST.md  # Comprehensive IEEE submission quality gate checklist
```

---

## Reproduction and Compilation

### 1. Requirements
- Python 3.10+ with packages: `pypdf`, `matplotlib`, `pytest`
- LaTeX compiler: `tectonic` (recommended, version 0.17+) or `pdflatex` / `xelatex` with standard TeXLive packages.

### 2. Verify Quantitative Claims
To verify that every single number reported in the manuscript matches the authoritative experimental logs:
```bash
python scripts/check_paper_numbers.py
```
This tool validates all 21 claims in `claims_registry.json` against the underlying raw JSON files in `logs/` and asserts zero missing placeholders.

### 3. Verify References and Secrets
```bash
python scripts/check_references.py
python scripts/check_no_secrets.py
```

### 4. Compile the PDF Manuscript
Compile the LaTeX source directly with Tectonic:
```bash
tectonic main.tex
```
Or with `pdflatex`:
```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```
The resulting `main.pdf` is strictly 6 pages in IEEE conference format.
