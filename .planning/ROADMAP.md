# TollgateRAG Research Roadmap & Phase Status

## Phase Overview

- [x] **Phase 1: Environment & Reproducibility Control** (Completed)
  - Pinned all dependencies in `requirements.txt` with exact pip freeze versions.
  - Hardened `.gitignore` and added pre-commit secret scanning hooks.
  - Fixed reference date (`REFERENCE_DATE = "2026-10-12"`) and global seeds (`SEED = 1234`).
  - Added master reproduction runner `scripts/reproduce.py`.

- [x] **Phase 2: Scoring Design & Combiner Overhaul** (Completed)
  - Replaced brittle weighted-sum cliff with Noisy-OR combiner: `risk = max(anchor_conflict, injection)` modulated by trust/freshness/authority.
  - Calibrated operational decision thresholds strictly on the held-out validation split (`logs/calibration.json`).
  - Added gate boundary tests in `tests/test_tollgaterag.py`.

- [x] **Phase 3: Sentence-Level Anchor NLI & True Batching** (Completed)
  - Upgraded anchor-conflict detector to sentence-level constraint matching via cosine similarity.
  - Implemented true batch evaluation in `batch_evaluate_nli()`.
  - Empirically verified DeBERTa-v3 cross-encoder label ordering.

- [x] **Phase 4: Latency Profiling & KPI Reconciliation** (Completed)
  - Profiled per-stage latency: warm median 716.4 ms for neural NLI on 12-core CPU.
  - Reconciled target vs. measured KPI claims.

- [x] **Phase 5: Benchmark Rigor & Split Disjointness** (Completed)
  - Expanded benchmark to 480 synthetic documents across 6 enterprise domains with balanced class distributions.
  - Created topic-disjoint train/val/test splits (`data/splits.json`).
  - Added `benign_hard` documents containing legitimate relaxation phrasing without contradictions.
  - Mapped document-anchor pairings in `data/pairs.json`.

- [x] **Phase 6: Raw-Text Baselines & SOTA Comparison** (Completed)
  - Re-implemented all baselines operating strictly on raw document text.
  - Evaluated real Meta Prompt Guard (`meta-llama/llama-prompt-guard-2-86m`) on Groq.
  - Authored verified related work review in `docs/RELATED_WORK.md`.

- [x] **Phase 7: PoisonedRAG Evaluation Protocol** (Completed)
  - Designed dual-protocol evaluation across HotpotQA, NQ, and MS MARCO:
    - Protocol A (Grounded reference anchors): 53.6% to 69.2% mitigation rate.
    - Protocol B (Ungrounded open-domain stress test): 0.0% mitigation, demonstrating necessity of verified anchor policies.

- [x] **Phase 8: Adaptive Red-Teaming with Real LLM Loop** (Completed)
  - Executed closed-loop iterative red-teaming across 30 target constraints.
  - Attacker: `openai/gpt-oss-120b` (Groq API, seed 1234, disk-cached).
  - Independent semantic judge: `qwen/qwen3.8-27b` (Groq API, seed 1234, disk-cached).
  - Measured Valid ASR: 6.7% (Black-Box), 13.3% (White-Box).

- [x] **Phase 9: Comprehensive Ablations** (Completed)
  - Conducted leave-one-out dimension ablations with zeroed weights and renormalized weights.
  - Conducted architectural ablations (`USE_NLI`, `USE_CUE_FALLBACK`, Noisy-OR vs. Weighted, anchor selection variants).

- [x] **Phase 10: Code Review & System Hardening** (Completed)
  - Integrated epistemic uncertainty caveats into LLM synthesis prompt for warned passages.
  - Implemented cryptographically tamper-evident SHA-256 provenance hash-chaining.
  - Fixed cross-platform CRLF regex in `ingest.py` and date parsing in `pdf_loader.py`.

- [x] **Phase 11: Extended Test Suite** (Completed)
  - 19 automated tests passing in `tests/test_tollgaterag.py`.

- [ ] **Phase 12: Documentation & Planning Alignment** (In Progress)
- [ ] **Phase 13: Formal Paper Rewrite & Verification Script** (Pending)
