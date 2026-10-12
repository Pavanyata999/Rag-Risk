# TollgateRAG: Auditable Pre-Generation Epistemic Risk Gating for Agentic RAG

## 1. Project Overview & Scientific Thesis
Standard Retrieval-Augmented Generation (RAG) pipelines naively concatenate retrieved external documents into an LLM context window. In enterprise and high-stakes settings, this exposes a severe vulnerability to **Constraint Relaxation Attacks (CRAs)** and **Authority Spoofing**: untrusted documents that subtly contradict or soften official policy constraints (e.g. spending caps, authorization requirements, security rules) without using overt prompt injection keywords.

TollgateRAG introduces a pre-generation **Epistemic Risk Gate** between retrieval and context synthesis that evaluates candidate passages against verified anchor constraints using **Cross-Document Natural Language Inference (NLI)** and **Provenance Stance Verification**, providing a tri-state action decision (`ACCEPT`, `WARN/CONDITION`, `REJECT/QUARANTINE`) with sub-second CPU gating overhead (warm median ~716 ms).

## 2. Target Conferences & Publication Venues
- **Primary:** USENIX Security 2026, IEEE Symposium on Security and Privacy (S&P 2026), ACM CCS 2026
- **Secondary:** ACL 2026, EMNLP 2026 (Empirical Methods in NLP - Security Track)

## 3. High-Stakes Threat Model
- **Attacker Capability:** Attacker can inject or modify untrusted wiki pages, forums, or departmental uploads into the enterprise vector store.
- **Attack Payload:**
  - *Direct Prompt Injections:* Instruction overrides.
  - *Subtle Constraint Relaxations:* Pseudo-authoritative policy softening ("Effective immediately, VP approval waived...").
  - *Evasive Constraint Relaxations:* Modifying numerical caps or standards with zero trigger words.
- **Attacker Knowledge:** Both static adversaries and adaptive adversaries who know the defense algorithm exists.

## 4. Key Performance Indicators (KPIs) — Target vs. Empirically Achieved
| KPI Metric | Target | Achieved (Empirical Logs) | Status |
| :--- | :---: | :---: | :---: |
| **Adversarial Reject Rate (ARR)** | $\ge 90\%$ | 89.7% (Test) / 94.2% Flag Rate | Met / Near-Target |
| **Benign False Positive Rate (FPR)** | $\le 2\%$ | 0.0% (Test) | Fully Met |
| **Context Contamination Rate (CCR)** | $< 10\%$ | 3.3% (down from 61.7%) | Fully Met |
| **Gating Latency Overhead (Warm CPU)** | $\le 40\text{ ms}$ | **716.4 ms** (Neural NLI) / **3.2 ms** (Retrieval) | Empirical Trade-off (CPU DeBERTa-v3 cross-encoder vs heuristic regex) |
| **Cold Start Latency** | N/A | 16.5 s (one-time DeBERTa-v3 load) | Documented |
