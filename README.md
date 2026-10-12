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
          [risk = max(anchor_conflict, injection) ⊕ modulation(trust, freshness, auth)]
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

## Empirical Benchmark Results

Evaluated on the **held-out test split** of the synthetic 480-document Enterprise Policy Benchmark across 6 domains (Travel, IT/Cloud, Procurement, HR, Legal, Code Review) across 24 test queries and 192 unseen documents (79 adversarial exposures, 13 benign, 12 benign-hard, 39 verified). All confidence intervals are **Wilson score 95% intervals**.

### Held-Out Test Split Comparison (`logs/eval_test_split.json`)

| Defense Mechanism | Adversarial Reject Rate [95% CI] | Benign FPR [95% CI] | Benign-Hard FPR [95% CI] | Context Contamination [95% CI] | Final Adv Docs in Context |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Plain RAG (No Gate)** | 0.0% [0.0% – 4.6%] | 0.0% [0.0% – 22.8%] | 0.0% [0.0% – 24.3%] | 91.7% [79.2% – 100.0%] | 31 |
| **Strict Whitelist** | 100.0% [95.4% – 100.0%] | **100.0%** [77.2% – 100.0%] | **100.0%** [75.8% – 100.0%] | 0.0% [0.0% – 0.0%] | 0 |
| **BIPIA Keyword Filter** | 5.1% [2.0% – 12.3%] | 0.0% [0.0% – 22.8%] | 0.0% [0.0% – 24.3%] | 91.7% [79.2% – 100.0%] | 31 |
| **Perplexity Filter** | 0.0% [0.0% – 4.6%] | 0.0% [0.0% – 22.8%] | 0.0% [0.0% – 24.3%] | 91.7% [79.2% – 100.0%] | 31 |
| **Prompt Guard (Meta 86M)** | 4.7% [1.3% – 14.8%] | 0.0% [0.0% – 22.8%] | 0.0% [0.0% – 24.3%] | 83.3% [64.2% – 93.3%] | 30 |
| **TollgateRAG (Weighted)** | 87.3% [78.2% – 93.0%] | 0.0% [0.0% – 22.8%] | 66.7% [39.1% – 86.2%] | 29.2% [12.5% – 50.0%] | 8 |
| **TollgateRAG (Noisy-OR - Default)** | **88.6%** [79.8% – 93.9%] | **0.0%** [0.0% – 22.8%] | **66.7%** [39.1% – 86.2%] | **29.2%** [12.5% – 50.0%] | **8** |

### Breakdown by Adversarial Attack Subtype (Noisy-OR on Test Split)
- **Subtle Constraint Relaxation:** **95.8%** [79.8% – 99.3%] rejected (23/24)
- **Evasive Numerical Alterations:** **72.0%** [52.4% – 85.7%] rejected (18/25)
- **Direct Prompt Injection:** **100.0%** [87.5% – 100.0%] rejected (27/27)
- **Paraphrased / Spelled-Out Numbers:** **66.7%** [20.8% – 93.9%] rejected (2/3)
- **Anchor Retrieval Recall:** **100.0%** [95.4% – 100.0%] (79/79 target anchors retrieved)

### Adaptive Red-Teaming (`logs/adaptive_redteam_results.json`)
Evaluated using a closed-loop iterative optimizer (N=10 rewrites) across all 30 benchmark constraints:
- **Attacker LLM:** `openai/gpt-oss-120b` (Groq API, seed 1234, disk-cached)
- **Independent Semantic Judge:** `qwen/qwen3.8-27b` (Groq API, seed 1234, disk-cached)
- **Black-Box Threat Model:** Raw evasion 100.0%, Valid ASR (meaning preserved) = **6.7%** [1.8% – 21.3%] (Avg queries: 1.9)
- **White-Box Threat Model:** Raw evasion 100.0%, Valid ASR (meaning preserved) = **13.3%** [5.3% – 29.7%] (Avg queries: 1.9)
- *Key Finding:* 86.7% to 93.3% of raw evasions succeeded only by deleting the policy violation entirely, which is rejected by the independent semantic judge.

### Latency Profile (AMD64 12-Core CPU, Warm Cache)
- **Dense Vector Retrieval:** 3.2 ms median
- **Anchor Constraint Selection:** 2.1 ms median
- **Sentence-Level DeBERTa-v3 NLI Scoring:** 716.4 ms median / 1,023.8 ms p95
- **Action Gate Decision:** 0.02 ms median
- **Total Pipeline (Extractive):** 721.7 ms median
- **Cold Start (Model Initialization):** 16.5 s (one-time load)

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

# On Linux/macOS:
source venv/bin/activate

# On Windows:
.\venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note on NLI Model:** The sentence-level cross-encoder (`cross-encoder/nli-deberta-v3-base`, ~400 MB) downloads automatically from Hugging Face on first execution. No Hugging Face API key is required.

### 3. Optional: Configure Remote LLM (Groq API)

For generative answer synthesis and adaptive red-teaming, copy the template and configure your Groq API key:

```bash
# Add to .env:
TOLLGATERAG_LLM_BASE_URL="https://api.groq.com/openai/v1"
TOLLGATERAG_LLM_API_KEY="your_groq_api_key_here"
```

All responses are cached on disk under `logs/llm_cache/` keyed by prompt SHA-256 hash for free, deterministic reruns.

---

## Reproducing All Experiments

You can reproduce all benchmark artifacts, split calibrations, baseline runs, red-team iterations, ablations, and figures with a single command:

```bash
# Using Python runner:
python scripts/reproduce.py

# Or using Make:
make reproduce
```

The master script executes the full verification pipeline:
1. `scripts/generate_large_benchmark.py`: Generates 480 synthetic policy documents with metadata parity and creates topic-disjoint splits (`data/splits.json`).
2. `tollgaterag/ingest.py`: Builds the Chroma vector index and TF-IDF fallback store.
3. `tollgaterag/calibrate.py`: Calibrates decision thresholds on the validation split (`logs/calibration.json`).
4. `tollgaterag/eval.py`: Evaluates the held-out test split with Wilson 95% CIs (`logs/eval_test_split.json`).
5. `tollgaterag/eval_baselines.py`: Evaluates raw-text baselines and Prompt Guard (`logs/sota_baselines_comparison.json`).
6. `tollgaterag/eval_poisonedrag.py`: Evaluates dual-protocol PoisonedRAG benchmarks (`logs/poisonedrag_eval_results.json`).
7. `tollgaterag/red_team.py`: Runs the closed-loop adaptive red-teaming harness (`logs/adaptive_redteam_results.json`).
8. `tollgaterag/ablation.py`: Executes leave-one-out and architectural ablations (`logs/ablation_results.json`).
9. `scripts/generate_paper_figures.py`: Generates publication figures in `docs/paper/figures/`.
10. `tollgaterag/excel_export.py`: Exports all metrics to `logs/tollgaterag_metrics.xlsx`.

Run tests at any time with:
```bash
pytest tests/ -q
```

---

## Honest Limitations & Threats to Validity

1. **Synthetic, Template-Generated Benchmark:** The 480-document evaluation corpus was synthetically constructed using domain templates. While topics and classes are partitioned across disjoint splits, real-world enterprise documents exhibit higher lexical diversity and formatting complexity.
2. **Self-Declared Trust Ingestion Labels:** TollgateRAG relies on trust classification (`verified` vs `unverified`) supplied at document ingestion. In an unhardened environment where an adversary can forge ingestion metadata, trust signals are compromised. Production deployments require cryptographic ingestion signing.
3. **Benign-Hard False Positive Trade-Off:** Legitimate unverified documents containing policy-like phrases ("effective immediately", "waived") incur a 66.7% false rejection rate on the test split due to lexical relaxation cues and similarity overlap with anchor topics.
4. **Anchor Retrieval Dependence:** TollgateRAG requires verified anchor policies covering the queried domain. On ungrounded open-domain datasets lacking authoritative anchors (e.g. open-domain PoisonedRAG), mitigation effectiveness is 0.0%.
5. **CPU Inference Latency:** Sentence-level cross-encoder NLI requires ~716 ms on a 12-core CPU, which exceeds the ideal sub-40 ms budget. Low-latency edge deployment requires GPU acceleration, ONNX runtime, or model distillation.
6. **English-Language Evaluation:** Lexical cue lists, regex patterns, and DeBERTa-v3 NLI checkpoints are tuned for English text; multilingual performance has not been validated.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
