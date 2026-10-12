# Changelog

All notable changes to the TollgateRAG research framework and evaluation suite are documented here.

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
