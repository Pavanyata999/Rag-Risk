# Changelog

All notable changes to the TollgateRAG research framework and evaluation suite are documented here.

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
