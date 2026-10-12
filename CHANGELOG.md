# Changelog

All notable changes to the TollgateRAG research framework and evaluation suite are documented here.

## [Phase 7: Defensible PoisonedRAG Evaluation Protocol & Sanity Verification] - 2026-10-12

### Added
- Redesigned `tollgaterag/eval_poisonedrag.py` from legacy flawed `anchors=[]` harness into a dual-protocol evaluation suite:
  - **Protocol A (Grounded Reference Setting)**: Each query is evaluated alongside an authenticated factual reference anchor. TollgateRAG achieves 53.6% reject on HotpotQA, 54.4% on Natural Questions (NQ), and 69.2% on MS MARCO.
  - **Protocol B (Ungrounded Open-Domain Stress Test)**: Evaluated in ungrounded setting without anchor context (`anchors=[]`). TollgateRAG achieves 0.0% reject across all datasets, honestly demonstrating that TollgateRAG is an anchor-grounded policy defense rather than an ungrounded open-domain hallucination filter.
- Added automated pre-evaluation sanity check (`sanity_check_harness()`) asserting that the test harness strictly rejects direct injections and explicit anchor contradictions before evaluating benchmark suites.
- Output results saved to `logs/poisonedrag_eval_results.json`.

### Verification
- `pytest tests/ -q`: 13 passed in 21.0s.
- `python -m tollgaterag.eval_poisonedrag`: Sanity check passed, dual-protocol metrics generated.



## [Phase 6: SOTA Baselines on Raw Document Text & Real Prompt Guard Model] - 2026-10-12

### Added
- Reimplemented all baseline defenses in `tollgaterag/baselines.py` and `tollgaterag/eval_baselines.py` to operate strictly on raw document text rather than pipeline sub-scores.
- Integrated real neural guardrail baseline: Meta AI's `meta-llama/llama-prompt-guard-2-86m` via Groq endpoint with on-disk response caching (`logs/llm_cache/`) and append-only audit logging (`logs/llm_audit.jsonl`).
- Implemented LLM-free heuristic baseline: TF-IDF / term-overlap anchor similarity + relaxation cue regex matching.
- Implemented Trust-Weighted Retrieval baseline: re-ranks candidate pool by penalizing unverified sources without hard rejection.
- Created `docs/RELATED_WORK.md`: taxonomic comparison of RAG defenses and literature review covering RAGShield (Patil, 2026), TrustRAG (2025), AegisRAG-RADMS (2025/2026), RobustRAG (USENIX Security 2024), and MAP-Graph (Wang et al., 2026) with verified citations.

### Changed
- Baseline performance evaluated on the held-out test split (24 queries, 192 docs) recorded in `logs/sota_baselines_comparison.json`:
  - Plain RAG (Unprotected): 0.0% Adv Reject, 87.5% Contamination.
  - Strict Whitelist (Zero Trust): 100.0% Adv Reject, 100.0% Benign FP (complete loss of unverified availability).
  - Keyword / BIPIA Filter: 4.7% Adv Reject, 0.0% Benign FP, 83.3% Contamination.
  - Perplexity / Anomaly Filter: 0.0% Adv Reject (adversarial documents are grammatically coherent).
  - Keyword Guardrail (Simulated): 1.6% Adv Reject (26.6% Flag), 87.5% Contamination.
  - Prompt Guard Real (Meta AI 86M): 4.7% Adv Reject (7.8% Flag), 83.3% Contamination (prompt guard is blind to subtle semantic constraint relaxations).
  - TF-IDF + Relaxation Cues: 21.9% Adv Reject, 100.0% Benign-Hard FP (indiscriminately blocks legitimate trigger words).
  - Trust-Weighted Retrieval: 0.0% Adv Reject, 87.5% Contamination.
  - TollgateRAG (Noisy-OR NLI Gate): 89.1% Adv Reject, 0.0% Clean Benign FP, 66.7% Benign-Hard FP, 25.0% Contamination.

### Verification
- `pytest tests/ -q`: 13 passed in 23.3s.
- `python -m tollgaterag.eval_baselines`: Generated `logs/sota_baselines_comparison.json`.
- `docs/RELATED_WORK.md`: Verified all citations and created comparative matrix.



## [Phase 5: Dataset & Evaluation Rigor - Topic-Disjoint Splits, Hard Negatives, & Wilson CIs] - 2026-10-12

### Added
- Expanded benchmark in `scripts/generate_large_benchmark.py` to 480 total documents across 6 domains and 30 topics.
- Eliminated metadata leakage: randomized `SOURCE` and `DATE` uniformly across all classes.
- Added 3 distinct phrasings per class per topic, including spelled-out numbers ("two hundred and fifty dollars") and multi-sentence relaxations.
- Introduced 60 `benign_hard` documents (legitimate unverified documents containing trigger words like "waived", "no longer required", "effective immediately" that conform to policy) and 30 `low_quality` documents (outdated/misinformed non-malicious).
- Generated `data/pairs.json` mapping every document to target anchor, topic, and attack type.
- Built topic-disjoint `data/splits.json` partitioning topics into train (6 topics, 96 docs), val (12 topics, 192 docs), and test (12 topics, 192 docs).
- Upgraded `tollgaterag/eval.py` to support:
  - Wilson 95% confidence intervals for all rates.
  - Bootstrap 95% confidence intervals over queries for contamination.
  - Per-attack-class breakdown (subtle, evasive, injection, paraphrased).
  - Explicit reporting of warn rate AND reject rate on benign and benign_hard documents.
  - Topic-disjoint held-out test evaluation (`logs/eval_test_split.json`) vs full corpus evaluation (`logs/eval_full_corpus.json`).
  - Anchor retrieval recall tracking (100% on test split).
- Refined `tollgaterag/calibrate.py` to optimize thresholds strictly on validation split with clean benign FPR <= 2%, logging sweep curve to `logs/calibration.json`.

### Changed
- Honest empirical metrics on held-out test split (24 queries, 192 documents):
  - Adversarial Reject Rate: 88.6% [95% CI: 79.8-93.9%] (down from legacy unpartitioned 96.2%).
  - Clean Benign FPR: 0.0% [95% CI: 0.0-9.4%].
  - Benign-Hard FPR (Stress test): 66.7% [95% CI: 39.1-86.2%].
  - Contamination: 29.2% [95% CI: 12.5-50.0%] (vs. 91.7% for Plain RAG).
- Full corpus metrics (60 queries, 480 documents):
  - Adversarial Reject Rate: 91.3% [95% CI: 86.7-94.4%].
  - Clean Benign FPR: 0.0% [95% CI: 0.0-3.9%].
  - Benign-Hard FPR: 62.5% [95% CI: 42.4-79.3%], Warn: 25.0%.
  - Contamination: 23.3% [95% CI: 13.3-35.0%] (vs. 90.0% for Plain RAG).

### Verification
- `pytest tests/ -q`: 13 passed in 21.8s.
- `python -m tollgaterag.calibrate`: Validation curve saved to `logs/calibration.json`.
- `python -m tollgaterag.eval test`: Saved to `logs/eval_test_split.json`.
- `python -m tollgaterag.eval full`: Saved to `logs/eval_full_corpus.json`.



## [Phase 4: Latency Profiling & Honest KPI Updates] - 2026-10-12

### Added
- Implemented stage-by-stage timing instrumentation in `tollgaterag/pipeline.py`: records `retrieval_ms`, `anchor_selection_ms`, `scoring_nli_ms`, `gating_ms`, and `generation_ms` per query.
- Created `tollgaterag/latency_benchmark.py` for automated cold start vs. warm benchmarking with host hardware profiling.
- Generated `logs/latency_benchmark.json` documenting exact execution speeds on AMD64 12-core CPU.

### Changed
- Replaced outdated "sub-40ms" claim in `.planning/PROJECT.md` with honest empirical measurements:
  - Cold Start: 16.5 s (one-time model weight initialization into memory).
  - Warm Gating Median: 716.4 ms (sentence-level DeBERTa-v3 cross-encoder on CPU).
  - Retrieval & Gating: 3.2 ms retrieval, 0.02 ms gating action determination.
  - End-to-end with remote LLM generation: 1,980.3 ms median.

### Verification
- `pytest tests/ -q`: 13 passed in 21.3s.
- `python -m tollgaterag.latency_benchmark`: Completed 30 warm query trials and recorded full stage percentiles.

## [Phase 3: Fix Anchor-Conflict Detector & Fine-Grained Sentence NLI] - 2026-10-12

### Added
- Upgraded `tollgaterag/nli_engine.py` with true batched prediction (`batch_evaluate_nli` collects all uncached pairs and executes a single model prediction pass) and evaluation count tracking.
- Implemented sentence-level constraint extraction (`_split_into_sentences`) and sentence-to-sentence cosine similarity matching in `tollgaterag/risk_scorer.py`.
- Added independent ablation switches `config.USE_NLI` and `config.USE_CUE_FALLBACK`.
- Enhanced `RiskReport` to track `selected_anchors` and `evaluated_pairs` count per candidate to compute `anchor_retrieval_recall`.
- Added unit tests: `test_nli_label_order_empirically` verifying DeBERTa-v3 label outputs on clear Entailment, Contradiction, and Neutral pairs, and `test_batch_evaluate_nli_matches_single_calls` verifying batch consistency.

### Changed
- Removed legacy heuristics in `_anchor_conflict`: eliminated crude document-level character truncation (600 chars), raw word overlap, and artificial `len(anchors) <= 3` / `anchors[:1]` special cases.
- Anchors are now selected via sentence-level constraint similarity matching, evaluating focused clause pairs.

### Verification
- `pytest tests/ -q`: 13 passed in 21.3s.

## [Phase 2: Fix Scoring Design & Combiner] - 2026-10-12

### Added
- Implemented Noisy-OR combiner in `tollgaterag/risk_scorer.py` (`combine()`): combines primary threat signals (`max(anchor_conflict, injection)`) with secondary modulating signals (`trust`, `freshness`, `authority`).
- Added configurable `config.COMBINER = "noisy_or" | "weighted"` allowing empirical comparison and logging.
- Added `config.get_config_dict()` for full parameter snapshots in all log artifacts.
- Created `tollgaterag/calibrate.py` to systematically calibrate operational decision thresholds strictly on the validation split, saving validation curve to `logs/calibration.json`.
- Added unit tests in `tests/test_tollgaterag.py` verifying that `anchor_conflict >= 0.9` alone triggers rejection and unverified benign trust alone (0.55) is not rejected.

### Changed
- Resolved the "ceiling at 0.4617" cliff where high-confidence NLI contradictions hovered marginally near 0.45 threshold.
- Preserved both combiner implementations for ablation comparisons.

### Verification
- `pytest tests/ -q`: 11 passed in 21.0s.
- `python -m tollgaterag.calibrate`: Completed validation sweep, saving curve to `logs/calibration.json`.

## [Phase 1: Reproducibility & Environment] - 2026-10-12

### Added
- Fixed reference date `REFERENCE_DATE = "2026-10-12"` in `tollgaterag/config.py` for deterministic freshness calculations.
- Seed control `SEED = 1234` and `set_seed()` in `tollgaterag/config.py` covering `random`, `numpy`, and `torch`.
- Probed Groq OpenAI-compatible API (`https://api.groq.com/openai/v1/models`) and logged 11 available models in `logs/groq_models_available.json` (including `meta-llama/llama-prompt-guard-2-86m`, `openai/gpt-oss-120b`, `qwen/qwen3.8-27b`).
- Pre-commit security check `scripts/check_no_secrets.py` and `.git/hooks/pre-commit` hook to prevent committing API keys.
- Master reproducibility runners: `Makefile` (`make reproduce`), `scripts/reproduce.sh`, and `scripts/reproduce.py`.

### Changed
- Refactored `tollgaterag/risk_scorer.py` `_freshness_risk()` to use `config.REFERENCE_DATE` instead of mutable `date.today()`.
- Pinned `requirements.txt` with exact package versions including `torch==2.8.0` and `sentence-transformers==6.1.0`.
- Hardened `.gitignore` to exclude `.env`, `**/.env`, `*.env`, `logs/provenance.jsonl`, `logs/review_queue.jsonl`, and local caches.

### Removed
- Cleaned up untracked `.agents/` and `skills-lock.json`.

### Verification
- `scripts/check_no_secrets.py`: PASSED (0 secrets detected).
- `pytest tests/ -q`: 9 passed in 21.5s.
