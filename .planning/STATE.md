# TollgateRAG Project State

## Current Active State
**MILESTONE: System Hardening & Empirical Reproducibility Overhaul (Phases 1-11 Complete)**

## Measured Empirical Metrics on Held-Out Test Split (`logs/eval_test_split.json`)
Evaluated across 24 queries and 192 documents in 24 unseen topics (79 adversarial exposures, 13 benign, 12 benign_hard, 39 verified):

| Defense Mechanism | Adversarial Reject Rate [95% CI] | Benign FPR [95% CI] | Benign-Hard FPR [95% CI] | Context Contamination [95% CI] |
| :--- | :---: | :---: | :---: | :---: |
| **Plain RAG (No Gate)** | 0.0% [0.0% – 4.6%] | 0.0% [0.0% – 22.8%] | 0.0% [0.0% – 24.3%] | 91.7% [79.2% – 100.0%] |
| **Strict Whitelist** | 100.0% [95.4% – 100.0%] | 100.0% [77.2% – 100.0%] | 100.0% [75.8% – 100.0%] | 0.0% [0.0% – 0.0%] |
| **BIPIA Keyword Filter** | 5.1% [2.0% – 12.3%] | 0.0% [0.0% – 22.8%] | 0.0% [0.0% – 24.3%] | 91.7% [79.2% – 100.0%] |
| **Perplexity Filter** | 0.0% [0.0% – 4.6%] | 0.0% [0.0% – 22.8%] | 0.0% [0.0% – 24.3%] | 91.7% [79.2% – 100.0%] |
| **Prompt Guard (Meta 86M)** | 4.7% [1.3% – 14.8%] | 0.0% [0.0% – 22.8%] | 0.0% [0.0% – 24.3%] | 83.3% [64.2% – 93.3%] |
| **TollgateRAG (Weighted)** | 87.3% [78.2% – 93.0%] | 0.0% [0.0% – 22.8%] | 66.7% [39.1% – 86.2%] | 29.2% [12.5% – 50.0%] |
| **TollgateRAG (Noisy-OR)** | **88.6%** [79.8% – 93.9%] | **0.0%** [0.0% – 22.8%] | **66.7%** [39.1% – 86.2%] | **29.2%** [12.5% – 50.0%] |

## Breakdown by Attack Subtype (Held-Out Test Split - Noisy-OR)
- **Subtle Constraint Relaxation:** 95.8% [79.8% – 99.3%] rejected (23/24)
- **Evasive Numerical Relaxation:** 72.0% [52.4% – 85.7%] rejected (18/25)
- **Direct Prompt Injection:** 100.0% [87.5% – 100.0%] rejected (27/27)
- **Paraphrased / Spelled-Out Numbers:** 66.7% [20.8% – 93.9%] rejected (2/3)

## Adaptive Red-Team Performance (`logs/adaptive_redteam_results.json`)
- **Attacker:** `openai/gpt-oss-120b` (N=10 iterations)
- **Independent Judge:** `qwen/qwen3.8-27b`
- **Black-Box Threat Model:** Raw evasion 100.0%, Valid ASR (meaning preserved) = **6.7%** [1.8% – 21.3%]
- **White-Box Threat Model:** Raw evasion 100.0%, Valid ASR (meaning preserved) = **13.3%** [5.3% – 29.7%]
