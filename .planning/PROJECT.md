# TollgateRAG: Auditable Pre-Generation Epistemic Risk Gating for Agentic RAG

## 1. Project Overview & Scientific Thesis
Standard Retrieval-Augmented Generation (RAG) pipelines naively concatenate retrieved external documents into an LLM context window. In enterprise and high-stakes settings, this exposes a severe vulnerability to **Constraint Relaxation Attacks (CRAs)** and **Authority Spoofing**: untrusted documents that subtly contradict or soften official policy constraints (e.g. spending caps, authorization requirements, security rules) without using overt prompt injection keywords.

TollgateRAG introduces a pre-generation **Epistemic Risk Gate** between retrieval and context synthesis that evaluates candidate passages against verified anchor constraints using **Cross-Document Natural Language Inference (NLI)** and **Provenance Stance Verification**, operating in **sub-40ms** to provide a tri-state action decision (`ACCEPT`, `WARN/CONDITION`, `REJECT/QUARANTINE`).

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

## 4. Key Performance Indicators (KPIs)
- **Adversarial Detection / Reject Rate:** $\ge 90\%$ on realistic enterprise attacks.
- **Benign False Positive Rate (FPR):** $\le 2\%$ on helpful unverified community tips (preserving utility).
- **Context Contamination Rate (CCR):** Reduced to $< 10\%$ (from $> 60\%$ in unprotected RAG).
- **Latency Overhead:** $\le 40\text{ ms}$ per retrieval query (usable in production).
