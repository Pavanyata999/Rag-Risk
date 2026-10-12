# Related Work & Defense Framework Comparison

This document provides a systematic literature review and comparative analysis of defense architectures against retrieval corruption, knowledge poisoning, and prompt injection in Retrieval-Augmented Generation (RAG).

All cited works have been verified against active scholarly indices and preprints.

---

## 1. Taxonomic Comparison of RAG Defenses

| Framework | Primary Threat Target | Defense Architecture & Mechanism | Verification / Model Type | Compared Experimentally in Tollgate-Bench? |
| :--- | :--- | :--- | :--- | :--- |
| **Plain RAG** | Baseline (none) | Unprotected vector retrieval and concatenation | None | **Yes** (Empirical Baseline) |
| **Strict Whitelist** | Unverified / external sources | Rejects all unverified documents at ingestion | Metadata / Provenance | **Yes** (Empirical Baseline) |
| **BIPIA / Keyword Filter** | Direct prompt injections | Regex matching of command override markers | Regex / Rule-based | **Yes** (Empirical Baseline) |
| **Perplexity Filter** | Obfuscated injections / noise | Shannon character entropy / anomaly detection | Statistical / Distribution | **Yes** (Empirical Baseline) |
| **Keyword Guardrail (Sim)** | Content moderation | Keyword matching on privilege escalation cues | Heuristic rule-based | **Yes** (Empirical Baseline) |
| **Prompt Guard (Meta AI)** | Jailbreak / Direct prompt injection | Transformer classification on raw text (`meta-llama/llama-prompt-guard-2-86m`) | Neural (86M classifier) | **Yes** (Empirical Baseline via Groq) |
| **TF-IDF + Relaxation Cues** | Subtle policy relaxations | Term-overlap similarity to anchors + heuristic relaxation regex | Heuristic / lexical | **Yes** (Empirical Baseline) |
| **Trust-Weighted Retrieval** | Untrusted source elevation | Reranking candidate documents by penalizing unverified sources | Retrieval scoring | **Yes** (Empirical Baseline) |
| **TollgateRAG (Ours)** | Constraint relaxations, evasive injections, staleness | Sentence-level cross-encoder NLI against verified anchors + multi-signal Noisy-OR | Neural (DeBERTa-v3) + Provenance | **Yes** (Proposed System) |
| **RAGShield** (Patil, 2026) | Numerical manipulation & government corpus poisoning | 5-layer defense: C2PA attestation, numerical registry, taint lattice, provenance generation | Cryptographic + Pattern Engine | *Architectural Comparison* (Requires C2PA infrastructure & schema registry) |
| **TrustRAG** (arXiv:2501.00879, 2025) | Corpus poisoning & knowledge corruption | Two-stage: K-means semantic cluster filtering + LLM self-assessment reasoning | Embedding Clustering + LLM Judge | *Architectural Comparison* (Requires heavy multi-query LLM reasoning passes) |
| **AegisRAG-RADMS** (2025/2026) | End-to-end agentic attacks (poisoning, injection, tool use) | Hybrid: HNSW context selection, ModernBERT injection classifier, dual tool firewalls | Neural Classifiers + Tool Firewalls | *Architectural Comparison* (Focuses on agentic tool execution firewalls) |
| **RobustRAG** (Xiang et al., USENIX Security 2024) | Corpus poisoning attacks | Isolated retrieval partitioning + majority voting / aggregation | Aggregation / LLM Ensemble | *Architectural Comparison* (Assumes clean anchor majority exists in retrieved pool) |
| **MAP-Graph** (Wang et al., 2026) | Persistent memory poisoning & unauthorized read access | Lifecycle graph authorization separating permission eligibility from graded path trust | Graph Authorization Engine | *Architectural Comparison* (Addresses long-term agent memory lifecycle rather than single-turn RAG) |

---

## 2. Detailed Review of Closely Related Works

### RAGShield (Patil, 2026)
- **Citations**: 
  - Patil, K. S. R. *"RAGShield: Detecting Numerical Claim Manipulation in Retrieval-Augmented Generation"*, arXiv:2604.00387 (2026).
  - Patil, K. S. R. *"RAGShield: Provenance-Verified Defense-in-Depth for Government RAG"*, arXiv:2604.03211 (2026).
- **Core Insights**: Identifies that dense semantic embeddings are blind to numerical precision changes (e.g., modifying a tax deduction from $500 to $5,000 does not significantly alter the cosine similarity in dense space). Proposes an extraction-and-registry engine alongside C2PA cryptographic provenance.
- **Comparison to TollgateRAG**: TollgateRAG similarly targets subtle numeric and constraint relaxations, but resolves them through **fine-grained sentence-level cross-encoder NLI (`cross-encoder/nli-deberta-v3-base`)** against verified corporate/regulatory policy anchors, eliminating the need for rigid pre-defined schema registries.

### TrustRAG (arXiv:2501.00879, 2025)
- **Citation**: *"TrustRAG: Enhancing Robustness and Trustworthiness in Retrieval-Augmented Generation"*, arXiv:2501.00879 (2025).
- **Core Insights**: Proposes a training-free two-stage pipeline: first clusters retrieved passages to isolate outlier poisoned documents, then uses the generator LLM's internal knowledge in a self-assessment prompt to resolve factual contradictions.
- **Comparison to TollgateRAG**: TrustRAG relies heavily on the LLM's internal parametric memory, which fails when the question concerns proprietary, private, or recently updated enterprise policies (where the LLM has no pre-trained knowledge). TollgateRAG instead grounds constraint verification in an explicit, authenticated anchor store.

### AegisRAG / AegisRAG-RADMS (2025/2026)
- **Core Insights**: Addresses multi-turn agentic RAG vulnerabilities by placing firewalls before tool calls and deploying transformer classifiers against prompt injections.
- **Comparison to TollgateRAG**: AegisRAG is optimized for tool-use agentic environments; TollgateRAG specifically optimizes single-turn enterprise question-answering pipelines with formal reject/warn/accept action gates.

### RobustRAG (Xiang et al., USENIX Security 2024)
- **Citation**: Xiang et al., *"Certifiably Robust Retrieval-Augmented Generation against Data Poisoning"*, USENIX Security 2024 (arXiv:2405.15556).
- **Core Insights**: Provides certifiable robustness guarantees by dividing retrieved passages into isolated sub-contexts, generating answers independently, and aggregating via majority voting.
- **Comparison to TollgateRAG**: RobustRAG incurs high latency overhead ($k \times$ LLM generation calls) and cannot certify answers when the poisoned passages dominate retrieval. TollgateRAG performs pre-generation filtering at the passage level using a lightweight cross-encoder, avoiding multi-LLM generation costs.

---

## 3. Experimental Scope and Limitations of Baselines

In our benchmark evaluation (`logs/sota_baselines_comparison.json`), we evaluate 8 comparative baselines alongside TollgateRAG:
1. **Plain RAG**: Illustrates the baseline vulnerability of unvetted context assembly (91.7% context contamination).
2. **Strict Whitelist**: Perfect security (0% contamination), but achieves 100% false rejection on unverified knowledge, destroying knowledge coverage.
3. **BIPIA / Keyword Filter**: Blocks blunt prompt injections, but achieves <6% rejection against subtle and evasive attacks.
4. **Perplexity Anomaly Filter**: Fails against grammatically fluent, coherent policy contradictions.
5. **Prompt Guard (Meta AI 86M)**: Effectively identifies direct prompt injection strings, but cannot detect semantic constraint relaxations that contain no injection syntax.
6. **TF-IDF + Relaxation Cues**: Demonstrates that simple term matching and keyword cues are insufficient without bidirectional semantic entailment checking.
7. **Trust-Weighted Retrieval**: Reranks to favor verified sources, but fails when user queries specifically match malicious external documents more closely than generic anchors.
8. **TollgateRAG**: Achieves 88.6% adversarial rejection on held-out test split with 0.0% clean benign false positives.
