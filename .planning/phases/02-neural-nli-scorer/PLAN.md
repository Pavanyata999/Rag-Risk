# Phase 2 Plan: Neural NLI & Epistemic Constraint Gating

## Objective
Replace brittle regex and keyword matching in `tollgaterag/risk_scorer.py` with a high-speed, lightweight Natural Language Inference (NLI) and semantic stance engine.

## Scientific Hypothesis
Constraint Relaxation Attacks (CRAs) and evasive policy fabrications present semantic contradictions to official anchor policies that cannot be captured by lexical overlap or regex. A dual-stream verifier (Semantic Stance + Entailment Contradiction) can detect $\ge 90\%$ of evasive and subtle policy relaxations while maintaining $< 2\%$ False Positive Rate on benign tips, running within a 40ms inference budget.

## Tasks
1. **Architecture & Model Selection (`tollgaterag/nli_engine.py`):**
   - Implement a fast NLI inference module using PyTorch / Transformers / Sentence-Transformers (e.g., `cross-encoder/nli-deberta-v3-small` or lightweight distilled NLI with local fallback).
   - Add batched pair-scoring `(anchor_sentence, candidate_sentence)` $\to$ `(entailment, neutral, contradiction)`.
2. **Anchor Policy Constraint Extractor (`tollgaterag/anchor_verifier.py`):**
   - For any unverified candidate retrieved by the vector store, select salient anchor sentences from matching domain anchors.
   - Run NLI verification:
     - If candidate *contradicts* an anchor statement (e.g. "approval waived" vs "requires approval", "$250" vs "$75"): Assign high `anchor_conflict` risk ($> 0.85$).
     - If candidate is *neutral* (e.g. benign travel tips, packing advice): Assign minimal `anchor_conflict` risk ($< 0.10$).
3. **Upgrade `tollgaterag/risk_scorer.py`:**
   - Integrate NLI anchor conflict scoring into composite risk calculation.
   - Maintain full audit logging with extracted contradiction reasoning in JSONL provenance log.
4. **Empirical Validation:**
   - Re-run `python -m tollgaterag.eval` across all 60 queries and 351 documents.
   - Target metrics: Adversarial Reject $\ge 90\%$, Benign FP $\le 2\%$, Latency $\le 40\text{ ms}$.
