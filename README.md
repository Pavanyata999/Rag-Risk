# TollgateRAG: Auditable Pre-Generation Epistemic Risk Gating for Agentic RAG

[![Tests](https://img.shields.io/badge/pytest-19%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)]()
[![Status](https://img.shields.io/badge/Status-Empirically%20Verified-blue.svg)]()

TollgateRAG introduces a pre-generation **Epistemic Risk Gate** positioned directly between retrieval and context synthesis in Retrieval-Augmented Generation (RAG) pipelines. It intercepts candidate passages and evaluates them against verified anchor constraints using **Sentence-Level Cross-Document Natural Language Inference (NLI)** and **Provenance Stance Verification**, assigning a deterministic tri-state action (`ACCEPT`, `WARN/CONDITION`, `REJECT/QUARANTINE`).

---

## Architecture & Gating Pipeline

```
User Query ──► Dense Retrieval (Top-6 Candidates)
                       │
                       ▼
         Epistemic Risk Scoring Engine
         ├── Trust Level & Ingestion Stance (w = 0.20)
         ├── Freshness Decay vs Reference Date (w = 0.05)
         ├── Injection Heuristic / Guardrail (w = 0.25)
         ├── Unauthorized Authority Claims (w = 0.15)
         └── Fine-Grained Sentence NLI vs Anchors (w = 0.35)
                       │
                       ▼
          Noisy-OR Risk Combiner
          [R = 1 - ∏(1 - w_i * s_i)]
                       │
                       ▼
            Tri-State Action Gate
          ┌────────────┬─────────────┬────────────┐
          ▼            ▼             ▼
       ACCEPT         WARN         REJECT
     (Admitted)   (Epistemic      (Quarantined)
                  Uncertainty)
                       │
                       ▼
         Top-3 Context ──► LLM Response Generation
                       │
                       ▼
        Tamper-Evident SHA-256 Provenance Audit Log
```

---

## Key Performance Indicators (KPI): Target vs. Measured

| Metric | Target | Measured (Held-Out Test Split) | Status | Log Source |
| :--- | :---: | :---: | :---: | :--- |
| **Adversarial Reject Rate (ARR)** | $\ge 90\%$ | **88.6%** [79.8% – 93.9%] | Near-Target | `logs/eval_test_split.json` |
| **Clean Benign False Positive Rate** | $\le 2\%$ | **0.0%** [0.0% – 22.8%] | Met | `logs/eval_test_split.json` |
| **Benign-Hard False Positive Rate** | $\le 10\%$ | **66.7%** [39.1% – 86.2%] | Unmet | `logs/eval_test_split.json` |
| **Context Contamination Rate** | $< 10\%$ | **29.2%** [12.5% – 50.0%] | Unmet | `logs/eval_test_split.json` |
| **Gating Latency (Warm CPU)** | $\le 40$ ms | **1,862.9 ms** (Median) | Unmet | `logs/latency_benchmark.json` |

*Note on Unmet Targets:* 
1. **Benign-Hard FPR (66.7%):** Legitimate unverified documents containing relaxation phrasing (e.g., procedural waivers like "manual mailing is waived") trigger genuine semantic contradiction against strict anchor policies. Tuning thresholds on validation demonstrates that lowering rejection thresholds to admit these passages reduces adversarial rejection to $\le 72.9\%$.
2. **Context Contamination (29.2%):** Reduced from 91.7% in Plain RAG, but full elimination requires complete recall across all adversarial variants.
3. **CPU Latency (1862.9 ms):** Sentence-level cross-encoder NLI (`cross-encoder/nli-deberta-v3-base`) requires dense multi-layer cross-attention; meeting sub-40 ms requires GPU acceleration or model distillation.

---

## Empirical Benchmark Results

Evaluated on the **held-out test split** of the synthetic 480-document Enterprise Policy Benchmark across 6 domains (Travel, IT/Cloud, Procurement, HR, Legal, Code Review) across 24 test queries and 192 unseen documents (79 adversarial exposures, 13 clean benign, 12 benign-hard, 39 verified anchors). All confidence intervals are **Wilson score 95% intervals**.

### Held-Out Test Split Comparison (`logs/eval_test_split.json`)

| Defense Mechanism | Adversarial Reject Rate [95% CI] | Clean Benign FPR [95% CI] | Benign-Hard FPR [95% CI] | Context Contamination [95% CI] | Final Adv Docs in Context |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Plain RAG (No Gate)** | 0.0% [0.0% – 4.6%] | 0.0% [0.0% – 22.8%] | 0.0% [0.0% – 24.3%] | 91.7% [79.2% – 100.0%] | 31 |
| **Strict Whitelist (Zero Trust)** | 100.0% [95.4% – 100.0%] | **100.0%** [77.2% – 100.0%] | **100.0%** [75.8% – 100.0%] | 0.0% [0.0% – 0.0%] | 0 |
| **BIPIA Keyword Filter** | 5.1% [2.0% – 12.3%] | 0.0% [0.0% – 22.8%] | 0.0% [0.0% – 24.3%] | 91.7% [79.2% – 100.0%] | 31 |
| **Perplexity Filter** | 0.0% [0.0% – 4.6%] | 0.0% [0.0% – 22.8%] | 0.0% [0.0% – 24.3%] | 91.7% [79.2% – 100.0%] | 31 |
| **Prompt Guard (Meta 86M)** | 4.7% [1.3% – 14.8%] | 0.0% [0.0% – 22.8%] | 0.0% [0.0% – 24.3%] | 83.3% [64.2% – 93.3%] | 30 |
| **TollgateRAG (Weighted Sum)** | 87.3% [78.2% – 93.0%] | 0.0% [0.0% – 22.8%] | 66.7% [39.1% – 86.2%] | 29.2% [12.5% – 50.0%] | 8 |
| **TollgateRAG (Noisy-OR - Default)** | **88.6%** [79.8% – 93.9%] | **0.0%** [0.0% – 22.8%] | **66.7%** [39.1% – 86.2%] | **29.2%** [12.5% – 50.0%] | **8** |

*Note on Sample Counts:* Because clean benign ($n=13$) and benign-hard ($n=12$) evaluate fewer than 30 exposures on the test split, their confidence intervals are wide and results should be considered indicative.

### Breakdown by Adversarial Attack Subtype (Held-Out Test Split)
- **Subtle Constraint Relaxation (CRAs):** **95.8%** [79.8% – 99.3%] rejected (23/24)
- **Evasive Numerical Alterations:** **72.0%** [52.4% – 85.7%] rejected (18/25)
- **Direct Prompt Injection:** **100.0%** [87.5% – 100.0%] rejected (27/27)
- **Paraphrased / Spelled-Out Numbers:** **66.7%** [20.8% – 93.9%] rejected (2/3)
- **Anchor Retrieval Recall:** **100.0%** [95.4% – 100.0%] (79/79 target anchors retrieved)

### Topic-Disjoint Resplit Stability (4 Random Partition Seeds) (`logs/resplit_results.json`)
- **Adversarial Reject Rate:** Mean = **92.5%** (Range: 90.9% – 94.1%)
- **Benign-Hard Reject Rate:** Mean = **66.0%** (Range: 50.0% – 100.0%)
- **Clean Benign False Positive Rate:** Mean = **0.0%** across all splits
- **Context Contamination:** Mean = **19.8%** (Range: 16.7% – 25.0%)

### Closed-Loop Adaptive Red-Teaming (`logs/adaptive_redteam_results.json`)
Evaluated using a closed-loop iterative optimizer ($N=10$ rounds) across all 30 benchmark constraints:
- **Attacker LLM:** `openai/gpt-oss-120b` (Groq API, seed 1234, disk-cached)
- **Independent Semantic Judge:** `qwen/qwen3.8-27b` (Groq API, seed 1234, disk-cached)
- **Black-Box Threat Model:** Raw evasion 100.0%, Valid ASR (meaning preserved) = **6.7%** [1.8% – 21.3%] (Avg queries: 1.9)
- **White-Box Threat Model:** Raw evasion 100.0%, Valid ASR (meaning preserved) = **13.3%** [5.3% – 29.7%] (Avg queries: 1.9)
- **Finding:** Over 86% of apparent filter evasions succeed only by deleting the policy violation entirely.
- **Judge Validation Study:** 40 cases sampled in `data/judge_validation.csv` awaiting manual human annotation (`scripts/judge_agreement.py`).

### PoisonedRAG Dual-Protocol Evaluation (`logs/poisonedrag_eval_results.json`)
Evaluated across 750 adversarial passages (150 questions) in HotpotQA, NQ, and MS MARCO:
- **Protocol A (Grounded Reference Anchors):** HotpotQA = 53.6%, NQ = 54.4%, MS MARCO = 69.2%
- **Protocol B (Ungrounded Open-Domain Stress Test):** 0.0% mitigation across all datasets, confirming that verified anchor grounding is an essential prerequisite.

### Stage Latency Profile (AMD64 12-Core CPU, 15 Warm Trials) (`logs/latency_benchmark.json`)
- **Dense Vector Retrieval:** 4.4 ms median (p95: 7.6 ms, mean: 5.0 ms)
- **Anchor Constraint Selection:** 0.0 ms median (cached)
- **Sentence-Level DeBERTa-v3 NLI Scoring:** 1,832.9 ms median (p95: 2,370.3 ms, mean: 1,581.3 ms)
- **Action Gate Decision:** 0.02 ms median (p95: 0.03 ms)
- **Total Gating Execution:** 1,862.9 ms median (p95: 2,571.2 ms, mean: 1,664.5 ms)
- **Cold Start (Model Initialization):** 17,275.7 ms (one-time load)

---

## Installation & Setup

### Prerequisites
- Python 3.11, 3.12, or 3.13
- Git

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/pradeepv777/Rag-Risk.git
cd Rag-Risk
python -m venv venv

# On Windows:
.\venv\Scripts\Activate.ps1

# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Variables & Security
TollgateRAG uses local DeBERTa-v3 cross-encoders for inference. For optional LLM baseline and red-teaming evaluations via Groq:
```bash
# Set environment variable (NEVER commit this key or hardcode in files)
$env:TOLLGATERAG_LLM_API_KEY="your_api_key_here"
```

---

## Reproduction & Verification Commands

All empirical figures and claims can be reproduced end-to-end:

```bash
# 1. Run all unit and integration tests
pytest tests/ -q

# 2. Verify zero secrets across history, tracked, and untracked files
python scripts/check_no_secrets.py

# 3. Verify every quantitative claim in the paper against raw logs
python scripts/check_paper_numbers.py

# 4. Audit bibliographic references against registries
python scripts/check_references.py

# 5. Build paper macros, tables, and check compilation
python scripts/build_paper.py
```

---

## Repository Structure

```
.
├── data/
│   ├── eval_queries.json           # 60 benchmark evaluation queries (30 topics)
│   ├── judge_validation.csv        # 40 sampled judge cases for human audit
│   ├── labels.json                 # Ground-truth passage labels
│   ├── pairs.json                  # Metadata and anchor bindings
│   └── splits.json                 # Topic-disjoint train/val/test split definitions
├── docs/
│   ├── benign_hard_analysis.md     # In-depth breakdown of 66.7% benign-hard FPR
│   └── paper/                      # Camera-ready IEEE conference LaTeX source & vector figures
├── logs/                           # Empirical logs (all paper numbers read from here)
│   ├── eval_test_split.json        # Main test split evaluation metrics
│   ├── sota_baselines_comparison.json
│   ├── ablation_results.json       # Ablation metrics on n=79 test exposures
│   ├── adaptive_redteam_results.json
│   ├── resplit_results.json        # 4-seed topic resplit stability analysis
│   └── latency_benchmark.json      # Stage-by-stage CPU latency profiling
├── scripts/                        # Autonomous reproduction & validation scripts
│   ├── build_paper.py              # Paper macro generator and compilation checker
│   ├── check_no_secrets.py         # Full git history secret scanner
│   ├── check_paper_numbers.py      # Exhaustive numeric claim verifier
│   ├── check_references.py         # Citation registry validator
│   └── reproduce.py                # Full pipeline reproduction runner
├── tollgaterag/                    # Core framework package
│   ├── ablation.py                 # Leave-one-out and architectural ablation engine
│   ├── config.py                   # Central configuration, seeds, and constants
│   ├── eval.py                     # Rigorous evaluation harness with Wilson CIs
│   ├── pipeline.py                 # End-to-end RAG inference and gating pipeline
│   ├── retriever.py                # ChromaDB dense retriever
│   └── risk_scorer.py              # Five-signal Noisy-OR risk engine
├── PAPER_CLAIMS.md                 # Complete audit mapping of paper numbers -> JSON keys
├── SUBMISSION_CHECKLIST.md         # Conference submission audit checklist
└── requirements.txt                # Pinned dependency specification
```
