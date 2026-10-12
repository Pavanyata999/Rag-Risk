# IEEE Conference Paper Submission Checklist: TollgateRAG

This checklist validates that the TollgateRAG research manuscript adheres to the rigorous requirements of top-tier academic computer science conferences (IEEE / USENIX / ACM format).

---

## 1. Manuscript Layout & Visual Hierarchy
- [x] **Page Count:** The compiled PDF (`research_paper/main.pdf`) is **strictly 6 pages**, complying with standard IEEE conference page limits.
- [x] **Two-Column Typography:** Professional IEEE conference format (`IEEEtran.cls`), balanced column heights, standard margins.
- [x] **Title & Abstract:** Crisp, descriptive title without hyperbolic claims. Evidence-based abstract stating problem, gap, method, key results (with exact denominators and 95% CIs), and primary limitation.
- [x] **Index Terms:** Canonical keywords: *Retrieval-Augmented Generation, AI Security, Indirect Prompt Injection, Natural Language Inference, Epistemic Gating*.
- [x] **Visual Elements:**
  - [x] **Fig. 1 (Architecture):** Publication-quality vector PDF diagram spanning both columns at the top of Page 2.
  - [x] **Fig. 2 (Pareto Sensitivity):** Operational trade-off curve on Page 4 illustrating ARR vs. Benign-Hard FPR across $\theta_{\text{rej}} \in [0.1, 0.9]$.
  - [x] **Fig. 3 (Adaptive Red-Team):** 10-round optimization dynamics on Page 5 contrasting raw filter bypass (100%) against valid meaning-preserved ASR (6.7% / 13.3%).
- [x] **Algorithm 1:** Implementation-faithful pseudocode listing (`algorithmic` environment) defining the complete decision procedure, tri-state action gating, and context backfill.

---

## 2. Mathematical Rigor & Notation
- [x] Formally defined notation: Query $q$, knowledge corpus $\mathcal{D} = \mathcal{D}_v \cup \mathcal{D}_u$, candidate pool $\mathcal{C}_q$, verified anchors $\mathcal{A}_q$.
- [x] Formally defined attacker objective: Maximizing retrieval while satisfying $R(d^*) < \theta_{\text{rej}}$ to cause constraint relaxation.
- [x] Formal definition of all five orthogonal risk signals: $s_{\text{trust}}, s_{\text{fresh}}, s_{\text{inj}}, s_{\text{auth}}, s_{\text{anchor}}$.
- [x] Formal cross-encoder sentence NLI equation and maximum contradiction aggregation.
- [x] Calibrated Noisy-OR formulation ($R_{\text{NOR}}$) and Weighted Sum formulation ($R_{\text{WS}}$) with exact parameter sensitivities.
- [x] Formal tri-state action gate (\textsc{Accept}, \textsc{Warn}, \textsc{Reject}) with validated thresholds ($\theta_{\text{warn}}=0.25, \theta_{\text{rej}}=0.45$).
- [x] Formal context assembly with retrieval backfill ($G_q^{\text{backfill}}$) and cryptographic hash-chain audit log ($h_t$).
- [x] Wilson score 95% confidence interval formula.

---

## 3. Empirical Accuracy & Reproducibility
- [x] **Zero Hand-Typed Numbers:** 100% of reported quantitative numbers in `main.tex` match authoritative raw JSON records in `logs/*.json`.
- [x] **Claims Registry:** 21/21 claims verified by `python scripts/check_paper_numbers.py` with zero failures.
- [x] **Zero Placeholders:** Zero unresolved `[MISSING]` or `TODO` placeholders in the manuscript.
- [x] **Zero Secrets:** `scripts/check_no_secrets.py` confirms 0 API keys or secret patterns across all git history, tracked files, staged diffs, and untracked files.
- [x] **100% Verified Citations:** All 14 BibTeX entries verified with authentic authors, venues, years, and stable URLs/DOIs via `scripts/check_references.py`.
- [x] **Unit Test Suite:** All 24 unit tests pass (`python -m pytest tests/ -q`).

---

## 4. Academic Integrity & Honest Scoping
- [x] **Benign-Hard Trade-off:** The 66.7% false positive rate on legitimate unverified documents with relaxation cues is prominently reported in the Abstract, Introduction, and Results.
- [x] **Synthetic Benchmark Scoping:** The synthetic nature of the 480-document corpus is transparently acknowledged.
- [x] **Human Trial Status:** Human judge agreement protocol is explicitly reported as pending ongoing trials (zero synthetic human labels).
- [x] **Fair Baseline Evaluation:** Prompt Guard and keyword filters are characterized as prompt-injection detectors not designed for policy relaxation, rather than strawman failures.
- [x] **Latency Trade-off:** CPU gating latency (median 1862.9 ms) is documented with profiling, noting the necessity of GPU/ONNX acceleration for real-time deployment.
