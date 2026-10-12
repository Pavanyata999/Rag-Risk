# TollgateRAG: Auditable Pre-Generation Epistemic Risk Gating for Agentic RAG

## 1. Project Overview & Scientific Thesis
Standard Retrieval-Augmented Generation (RAG) pipelines naively concatenate retrieved external documents into an LLM context window. In enterprise and high-stakes settings, this exposes a severe vulnerability to **Constraint Relaxation Attacks (CRAs)** and **Authority Spoofing**: untrusted documents that subtly contradict or soften official policy constraints (e.g., spending caps, authorization requirements, security rules) without using overt prompt injection keywords.

TollgateRAG introduces a pre-generation **Epistemic Risk Gate** between retrieval and context synthesis that evaluates candidate passages against verified anchor constraints using **Sentence-Level Cross-Document Natural Language Inference (NLI)** and **Provenance Stance Verification**, providing a tri-state action decision (`ACCEPT`, `WARN/CONDITION`, `REJECT/QUARANTINE`) with empirical CPU gating latency.

## 2. Benchmark Corpus & Protocol
- **Dataset Size:** 480 synthetic, template-generated enterprise policy documents across 6 high-stakes domains (Travel, IT/Cloud, Procurement, HR, Legal, Code Review).
- **Split Protocol:** Topic-disjoint partitions:
  - **Train:** 96 documents (12 topics)
  - **Validation (Calibration):** 192 documents (24 topics)
  - **Test (Held-out Evaluation):** 192 documents (24 topics, 24 queries, 79 adversarial candidate exposures)
- **Metadata Parity:** Document sources and dates are randomized across all classes to prevent spurious correlation or trivial metadata leakage.

## 3. High-Stakes Threat Model
- **Attacker Capability:** Attacker can inject untrusted documents into the enterprise knowledge base or web retrieval space.
- **Attack Subtypes:**
  - *Direct Prompt Injections:* System instruction overrides.
  - *Subtle Constraint Relaxations:* Pseudo-authoritative policy softening ("Effective immediately, VP approval waived...").
  - *Evasive Constraint Relaxations:* Numerical cap alterations with zero explicit injection cues.
  - *Paraphrased Attacks:* Spelled-out numbers and split-sentence relaxations.
- **Attacker Knowledge:** Static adversaries, Black-Box adaptive attackers (querying gate decisions), and White-Box adaptive attackers (inspecting risk sub-scores).

## 4. Key Performance Indicators (KPIs) — Target vs. Empirically Measured
All test split figures are computed with 95% Wilson score confidence intervals from `logs/eval_test_split.json`.

| KPI Metric | Target | Measured (Held-Out Test Split) | Status / Analysis |
| :--- | :---: | :---: | :---: |
| **Adversarial Reject Rate (ARR)** | $\ge 90\%$ | **88.6%** [79.8% – 93.9%] (70/79 rejected) | Near target; within 95% CI band |
| **Adversarial Flag Rate (ARR + Warn)** | $\ge 95\%$ | **88.6%** [79.8% – 93.9%] | Near target |
| **Benign FPR (Plain Benign)** | $\le 2\%$ | **0.0%** [0.0% – 22.8%] (0/13 rejected) | Fully met |
| **Benign-Hard FPR (Lexical Overlap)** | $\le 10\%$ | **66.7%** [39.1% – 86.2%] (8/12 rejected) | Unmet; critical trade-off between relaxation-cue heuristics and lexical overlap |
| **Context Contamination Rate (CCR)** | $< 10\%$ | **29.2%** [12.5% – 50.0%] (reduced from 91.7%) | Significant reduction (68% relative decrease), but above 10% target |
| **Anchor Retrieval Recall** | $\ge 95\%$ | **100.0%** [95.4% – 100.0%] (79/79 hits) | Fully met via similarity search |
| **Gating Latency Overhead (Warm CPU)** | $\le 40\text{ ms}$ | **716.4 ms** (Median) / **1,023.8 ms** (p95) | Unmet; CPU DeBERTa-v3 cross-encoder constraint scoring cannot meet 40 ms without GPU/quantization |
| **Retrieval & Action Latency (Warm)** | $\le 10\text{ ms}$ | **3.2 ms** (Retrieval) / **0.02 ms** (Action Gate) | Fully met |
| **Cold Start Latency** | N/A | **16.5 s** (Model initialization) | Documented overhead |
