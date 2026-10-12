# Conference Submission Readiness Checklist (`SUBMISSION_CHECKLIST.md`)

This checklist audits the submission package for conference review readiness.

---

## 1. Venue & Page Count
- **Target Format:** IEEE Two-Column Conference Style (`IEEEtran.cls` `[conference]`).
- **Venue:** Unspecified in prompt (Standard IEEE conference: 6–8 pages plus references).
  > **Note for Author:** If your target venue is IEEE S&P (12 pages), IEEE EuroS&P (10 pages), IEEE IRI (6-8 pages), or a specific workshop (4-6 pages), please confirm your venue.
- **Current Page Count:** ~7 pages formatted in two-column IEEEtran style.
- **Status:** READY FOR VENUE SPECIFICATION.

---

## 2. Anonymization & Double-Blind Review
- **Author Block:** Configured with author block from `docs/paper/AUTHORS.md`.
  - For double-blind review venues, replace `\author{...}` with `\author{\IEEEauthorblockN{Anonymous Authors}\IEEEauthorblockA{Anonymous Institution}}`.
  - No acknowledgments or internal lab names are included.
- **Code Repository Links:** Generic placeholders and anonymous artifact bundle references provided.
- **Status:** PASS (configurable for single-blind or double-blind).

---

## 3. Font Embedding & Vector Standards (`pdffonts`)
- **PDF Fonts:** All vector figures (`fig_sota_comparison.pdf`, `fig_pareto_threshold.pdf`, `fig_adaptive_redteam.pdf`, `fig_ablation.pdf`) are generated via Matplotlib with Type 42/TrueType embedded vector fonts.
- **Raster Figures:** Fallback PNG figures generated at 300 DPI for high-resolution printing.
- **Verification Command:** `pdffonts docs/paper/main.pdf`
- **Status:** PASS (all fonts embedded in vector PDFs).

---

## 4. Figure Legibility & Colors
- **Palette:** Colorblind-friendly, high-contrast Seaborn whitegrid palette (`#1f77b4` blue, `#d62728` red, `#2ca02c` green, `#ff7f0e` orange).
- **Typography:** Minimum 9pt font size on all annotations, tick marks, and axis titles for readability in print.
- **Format:** Dual vector `.pdf` and 300-DPI `.png` in `docs/paper/figures/`.
- **Status:** PASS.

---

## 5. Bibliographic Completeness & Integrity
- **BibTeX File:** `docs/paper/references.bib`
- **Audit Tool:** `scripts/check_references.py`
- **Audit Output:** `docs/paper/references_verification.md`
- **Result:** 14 out of 14 citations audited and verified against published conference proceedings, DOIs, or arXiv preprints.
- **Invented Citations:** Zero (0).
- **Status:** PASS.

---

## 6. AI Assistance Disclosure
- **Location:** Dedicated subsection `AI Assistance Disclosure` preceding References.
- **Text:** "AI tools were used for code refactoring, experiment orchestration, and LaTeX formatting under direct author supervision. All experimental results, logs, and conclusions were empirically generated and verified."
- **Status:** PASS.

---

## 7. Artifact Links & Data Availability
- **Reproducibility Script:** `python scripts/reproduce.py`
- **Verification Script:** `python scripts/check_paper_numbers.py`
- **Secrets Scanning:** `python scripts/check_no_secrets.py`
- **Bundles:** `arxiv_bundle.zip` and `supplementary.zip` contain verified, secret-free artifacts.
- **Status:** PASS.
