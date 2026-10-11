# Phase 3 Plan: SOTA Baselines & Adaptive Red-Teaming

## Objective
Implement standardized RAG security baselines from literature (Perplexity Filtering, Prompt Guardrails, Whitelisting) and build an automated Adaptive Red-Teaming loop to prove TollgateRAG's resilience against an attacker who attempts to evade NLI constraint detection.

## Baselines to Implement (`tollgaterag/baselines.py`):
1. **Unprotected Dense RAG:** Standard retrieval with zero pre-generation gating.
2. **Strict Provenance Whitelisting (Zero Trust):** Binary filter allowing only `verified` sources.
3. **Boundary / Injection Marker Filter (BIPIA baseline):** Keyword and delimiter regex filtering.
4. **Perplexity Anomaly Filter (PPL-Filter):** N-gram statistical anomaly and character entropy filtering.
5. **Prompt-Level Guardrail (Llama-Guard / NeMo Guardrail):** Content moderation policy evaluation.

## Adaptive Attacker Loop (`tollgaterag/red_team.py`):
- Formulate an adaptive adversary who knows the NLI gate is active.
- Employs 4 evasive strategies:
  - *Lexical Obfuscation:* Replacing policy terms with indirect synonyms.
  - *Constraint Splitting:* Spreading condition and action across distantly spaced clauses.
  - *Authority Mimicry:* Inserting formal institutional boilerplate without trigger tokens.
  - *Plausible Deniability / Hedging:* Phrasing relaxations as tentative standard interpretations.
- Evaluates the defense degradation curve under adaptive optimization.

## Verification Gate:
- Comparative benchmark running across all 60 queries.
- Measure Attack Success Rate (ASR), Context Contamination Rate (CCR), and False Positive Rate (FPR) across all baselines.
