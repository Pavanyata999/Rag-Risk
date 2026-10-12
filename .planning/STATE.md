# TollgateRAG Project State

## Current Active State
**MILESTONE: Final Independent Verification & Deliverables (Steps 1-9)**

## Key Performance Indicators (KPI): Target vs. Measured

| Metric | Target | Measured (Held-Out Test Split) | Status | Log Source |
| :--- | :---: | :---: | :---: | :--- |
| **Adversarial Reject Rate (ARR)** | $\ge 90\%$ | **88.6%** [79.8% – 93.9%] | Near-Target | `logs/eval_test_split.json` |
| **Clean Benign False Positive Rate** | $\le 2\%$ | **0.0%** [0.0% – 22.8%] | Met | `logs/eval_test_split.json` |
| **Benign-Hard False Positive Rate** | $\le 10\%$ | **66.7%** [39.1% – 86.2%] | Unmet | `logs/eval_test_split.json` |
| **Context Contamination Rate** | $< 10\%$ | **29.2%** [12.5% – 50.0%] | Unmet | `logs/eval_test_split.json` |
| **Gating Latency (Warm CPU)** | $\le 40$ ms | **1,862.9 ms** (Median) | Unmet | `logs/latency_benchmark.json` |

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

## Topic-Disjoint Resplit Stability (4 Random Partition Seeds) (`logs/resplit_results.json`)
- **Adversarial Reject Rate:** Mean = 92.5% (Range: 90.9% – 94.1%)
- **Benign-Hard Reject Rate:** Mean = 66.0% (Range: 50.0% – 100.0%)
- **Clean Benign False Positive Rate:** Mean = 0.0% across all splits
- **Context Contamination:** Mean = 19.8% (Range: 16.7% – 25.0%)

## Adaptive Red-Team Performance (`logs/adaptive_redteam_results.json`)
- **Attacker:** `openai/gpt-oss-120b` (N=10 iterations)
- **Independent Judge:** `qwen/qwen3.8-27b`
- **Black-Box Threat Model:** Raw evasion 100.0%, Valid ASR (meaning preserved) = **6.7%** [1.8% – 21.3%]
- **White-Box Threat Model:** Raw evasion 100.0%, Valid ASR (meaning preserved) = **13.3%** [5.3% – 29.7%]

## Stage Latency Profile (AMD64 12-Core CPU, 15 Warm Trials) (`logs/latency_benchmark.json`)
- **Dense Vector Retrieval:** 4.4 ms median (p95: 7.6 ms, mean: 5.0 ms)
- **Anchor Constraint Selection:** 0.0 ms median
- **Sentence-Level DeBERTa-v3 NLI Scoring:** 1,832.9 ms median (p95: 2,370.3 ms, mean: 1,581.3 ms)
- **Total Gating Execution:** 1,862.9 ms median (p95: 2,571.2 ms, mean: 1,664.5 ms)
- **Cold Start (Model Initialization):** 17,275.7 ms
