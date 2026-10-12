# Paper Quantitative Claims Audit Registry (`PAPER_CLAIMS.md`)

This registry audits and maps every quantitative result claim presented in the paper (`docs/paper/main.tex` and accompanying tables) directly to its source empirical log file and JSON key.

All claims are derived from scripts executed on the test system. Zero numbers are hand-typed.

---

## 1. Held-Out Test Split Primary Results

| Claim in Paper | Value & 95% Wilson CI | Log File | JSON Path / Key |
|:---|:---:|:---|:---|
| **Adversarial Reject Rate (TollgateRAG Noisy-OR)** | 88.6% [79.8%--93.9%] | `logs/eval_test_split.json` | `results["TollgateRAG (Noisy-OR combiner - Default)"]["adversarial_metrics"]["reject_rate"]` & `["reject_ci_95"]` |
| **Clean Benign False Positive Rate** | 0.0% [0.0%--22.8%] | `logs/eval_test_split.json` | `results["TollgateRAG (Noisy-OR combiner - Default)"]["benign_metrics"]["reject_rate"]` & `["reject_ci_95"]` |
| **Benign-Hard False Positive Rate** | 66.7% [39.1%--86.2%] | `logs/eval_test_split.json` | `results["TollgateRAG (Noisy-OR combiner - Default)"]["benign_hard_metrics"]["reject_rate"]` & `["reject_ci_95"]` |
| **Context Contamination (TollgateRAG)** | 29.2% [12.5%--50.0%] | `logs/eval_test_split.json` | `results["TollgateRAG (Noisy-OR combiner - Default)"]["contamination_metrics"]["contamination_rate"]` & `["contamination_ci_95"]` |
| **Context Contamination (Plain RAG)** | 91.7% [79.2%--100.0%] | `logs/eval_test_split.json` | `results["Plain RAG (no gate)"]["contamination_metrics"]["contamination_rate"]` & `["contamination_ci_95"]` |
| **Adversarial Docs in Context (TollgateRAG vs Plain RAG)** | 8 vs 31 | `logs/eval_test_split.json` | `results[...]["contamination_metrics"]["adversarial_docs_in_context"]` |
| **Anchor Retrieval Recall** | 100.0% [95.4%--100.0%] | `logs/eval_test_split.json` | `results["TollgateRAG (Noisy-OR combiner - Default)"]["anchor_retrieval_metrics"]["recall"]` |

---

## 2. Attack Subtype Breakdown (Held-Out Test Split)

| Attack Class | Events | Rejection Rate [95% CI] | Log File | JSON Path / Key |
|:---|:---:|:---:|:---|:---|
| **Subtle Constraint Relaxation Attacks (CRAs)** | 24 | 95.8% [79.8%--99.3%] | `logs/eval_test_split.json` | `adversarial_metrics["by_attack_subtype"]["subtle"]` |
| **Evasive Numerical Alterations** | 25 | 72.0% [52.4%--85.7%] | `logs/eval_test_split.json` | `adversarial_metrics["by_attack_subtype"]["evasive"]` |
| **Direct Prompt Injections** | 27 | 100.0% [87.5%--100.0%] | `logs/eval_test_split.json` | `adversarial_metrics["by_attack_subtype"]["injection"]` |
| **Paraphrased Numerical Alterations** | 3 | 66.7% [20.8%--93.9%] | `logs/eval_test_split.json` | `adversarial_metrics["by_attack_subtype"]["paraphrased"]` |

---

## 3. Comparative Baseline Benchmarks

| Defense Baseline | Rejection Rate [95% CI] | Benign FPR [95% CI] | Contamination | Log File | JSON Path |
|:---|:---:|:---:|:---:|:---|:---|
| **Plain RAG (Unprotected)** | 0.0% [0.0%--4.6%] | 0.0% [0.0%--22.8%] | 91.7% | `logs/sota_baselines_comparison.json` | `results["1. Plain RAG (Unprotected)"]` |
| **Strict Whitelist (Zero Trust)** | 100.0% [95.4%--100.0%] | 100.0% [77.2%--100.0%] | 0.0% | `logs/sota_baselines_comparison.json` | `results["2. Strict Whitelist (Zero Trust)"]` |
| **BIPIA Keyword Filter** | 5.1% [2.0%--12.3%] | 0.0% [0.0%--22.8%] | 91.7% | `logs/sota_baselines_comparison.json` | `results["3. Keyword / BIPIA Filter"]` |
| **Perplexity Filter** | 0.0% [0.0%--4.6%] | 0.0% [0.0%--22.8%] | 91.7% | `logs/sota_baselines_comparison.json` | `results["4. Perplexity Filter"]` |
| **Prompt Guard 86M (Meta AI)** | 4.7% [1.3--14.8%] | 0.0% [0.0%--22.8%] | 83.3% | `logs/sota_baselines_comparison.json` | `results["6. Prompt Guard Real (Meta AI 86M)"]` |
| **TollgateRAG (Weighted Sum)** | 87.3% [78.2%--93.0%] | 0.0% [0.0%--22.8%] | 29.2% | `logs/sota_baselines_comparison.json` | `results["7. TollgateRAG (Weighted combiner)"]` |
| **TollgateRAG (Noisy-OR Default)** | 88.6% [79.8%--93.9%] | 0.0% [0.0%--22.8%] | 29.2% | `logs/sota_baselines_comparison.json` | `results["8. TollgateRAG (Noisy-OR NLI Gate)"]` |

---

## 4. Closed-Loop Adaptive Red-Teaming

| Metric / Setting | Measured Value | Log File | JSON Path / Key |
|:---|:---:|:---|:---|
| **Black-Box Raw Filter Evasion Rate** | 100.0% | `logs/adaptive_redteam_results.json` | `settings["black_box"]["raw_evasion_rate"]` |
| **Black-Box Valid Attack Success Rate (ASR)** | 6.7% [1.8%--21.3%] | `logs/adaptive_redteam_results.json` | `settings["black_box"]["meaning_preserved_asr"]` & `["meaning_preserved_asr_ci"]` |
| **White-Box Raw Filter Evasion Rate** | 100.0% | `logs/adaptive_redteam_results.json` | `settings["white_box"]["raw_evasion_rate"]` |
| **White-Box Valid Attack Success Rate (ASR)** | 13.3% [5.3%--29.7%] | `logs/adaptive_redteam_results.json` | `settings["white_box"]["meaning_preserved_asr"]` & `["meaning_preserved_asr_ci"]` |
| **Attacker Query Budget & Convergence** | Up to 10 rounds (Mean 1.9) | `logs/adaptive_redteam_results.json` | `settings["black_box"]["avg_queries_per_case"]` |
| **Capitulation Rate (Evasion by Deleting Attack)** | 86.7% | `logs/adaptive_redteam_results.json` | `1.0 - settings["white_box"]["meaning_preserved_asr"]` |

---

## 5. PoisonedRAG Dual Protocol Evaluation

| Dataset & Protocol | Mitigation Rate | Passages / Questions | Log File | JSON Path / Key |
|:---|:---:|:---:|:---|:---|
| **HotpotQA (Protocol A - Grounded Anchors)** | 53.6% [47.4%--59.7%] | 250 / 50 | `logs/poisonedrag_eval_results.json` | `datasets["HotpotQA (Multi-hop)"]["protocol_a_grounded"]["reject_rate"]` |
| **NQ (Protocol A - Grounded Anchors)** | 54.4% [48.2%--60.5%] | 250 / 50 | `logs/poisonedrag_eval_results.json` | `datasets["Natural Questions (NQ)"]["protocol_a_grounded"]["reject_rate"]` |
| **MS MARCO (Protocol A - Grounded Anchors)** | 69.2% [63.2%--74.6%] | 250 / 50 | `logs/poisonedrag_eval_results.json` | `datasets["MS MARCO (Passage QA)"]["protocol_a_grounded"]["reject_rate"]` |
| **Protocol B (Ungrounded Open-Domain Stress Test)** | 0.0% [0.0%--1.5%] | 750 / 150 | `logs/poisonedrag_eval_results.json` | `datasets[...]["protocol_b_ungrounded_stress_test"]["reject_rate"]` |

---

## 6. Comprehensive Ablations ($n=79$ Test Exposures)

| Configuration / Variant | Adversarial Reject | Clean FP | Contamination | Log File | JSON Entry |
|:---|:---:|:---:|:---:|:---|:---|
| **Full Model (Default Noisy-OR)** | 88.6% [79.8%--93.9%] | 0.0% | 29.2% | `logs/ablation_results.json` | `leave_one_out_ablation[0]` |
| **Combiner: Weighted Sum** | 87.3% [78.2%--93.0%] | 0.0% | 29.2% | `logs/ablation_results.json` | `architectural_ablations[0]` |
| **w/o Anchor Conflict ($w_i=0$)** | 5.1% [1.8%--12.3%] | 0.0% | 83.3% | `logs/ablation_results.json` | `leave_one_out_ablation[1]` |
| **w/o Neural NLI (Cues Only)** | 31.6% [22.4%--42.6%] | 0.0% | 75.0% | `logs/ablation_results.json` | `architectural_ablations[1]` |
| **w/o Cue Fallback (NLI Only)** | 84.8% [75.3%--91.1%] | 0.0% | 37.5% | `logs/ablation_results.json` | `architectural_ablations[2]` |
| **Anchor Selection: Top-1** | 78.5% [68.2%--86.1%] | 0.0% | 37.5% | `logs/ablation_results.json` | `architectural_ablations[3]` |
| **Anchor Selection: Top-5 (Validation Opt)** | 93.7% [86.0%--97.3%] | 0.0% | 25.0% | `logs/ablation_results.json` | `architectural_ablations[6]` |

---

## 7. Latency Benchmark Profile (AMD64 12-Core CPU)

| Pipeline Stage | Median Latency | p95 Latency | Mean Latency | Log File | JSON Key |
|:---|:---:|:---:|:---:|:---|:---|
| **Dense Retrieval** | 4.4 ms | 7.6 ms | 5.0 ms | `logs/latency_benchmark.json` | `warm_runs.stage_breakdown_median_ms.retrieval_ms` |
| **Anchor Selection** | 0.0 ms | 0.0 ms | 0.0 ms | `logs/latency_benchmark.json` | `warm_runs.stage_breakdown_median_ms.anchor_selection_ms` |
| **Sentence NLI Scoring (DeBERTa-v3)** | 1832.9 ms | 2370.3 ms | 1581.3 ms | `logs/latency_benchmark.json` | `warm_runs.stage_breakdown_median_ms.scoring_nli_ms` |
| **Tri-State Action Gate** | 0.02 ms | 0.03 ms | 0.02 ms | `logs/latency_benchmark.json` | `warm_runs.stage_breakdown_median_ms.gating_ms` |
| **Total Gating Execution** | 1862.9 ms | 2571.2 ms | 1664.5 ms | `logs/latency_benchmark.json` | `warm_runs.median_ms` |
| **Cold Start Initialization** | 17275.7 ms | -- | -- | `logs/latency_benchmark.json` | `cold_start.total_ms` |

---

## 8. Topic-Disjoint Resplit Stability (4 Independent Seeds)

| Metric Across Splits | Mean | Min | Max | Log File | JSON Key |
|:---|:---:|:---:|:---:|:---|:---|
| **Adversarial Reject Rate (ARR)** | 92.5% | 90.9% | 94.1% | `logs/resplit_results.json` | `summary.adversarial_reject` |
| **Benign-Hard Reject Rate** | 66.0% | 50.0% | 100.0% | `logs/resplit_results.json` | `summary.benign_hard_reject` |
| **Clean Benign False Positive Rate** | 0.0% | 0.0% | 0.0% | `logs/resplit_results.json` | `summary.clean_benign_reject` |
| **Context Contamination** | 19.8% | 16.7% | 25.0% | `logs/resplit_results.json` | `summary.contamination` |
