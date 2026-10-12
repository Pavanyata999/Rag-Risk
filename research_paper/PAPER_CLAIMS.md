# TollgateRAG Research Claims & Evidence Registry

This document establishes the empirical traceability matrix connecting every quantitative claim in the TollgateRAG research manuscript (`main.tex`, `main.pdf`) to its underlying authoritative experimental log in `logs/*.json`.

---

## 1. Traceability Matrix

| Claim ID | Metric Definition | Manuscript Location | Source Log File | JSON Selector Path | Value | 95% Confidence Interval |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **c01** | Total synthetic corpus documents | Abstract, Sec. IV-A | `logs/benchmark_manifest.json` | `["total_documents"]` | **480** | N/A |
| **c02** | Held-out test queries | Abstract, Sec. IV-A, Tab. I | `logs/eval_test_split.json` | `["query_count"]` | **24** | N/A |
| **c03** | Test adversarial exposures | Sec. IV-C, Tab. I, Tab. II | `logs/eval_test_split.json` | `["results"]["TollgateRAG (Noisy-OR)"]["adversarial_metrics"]["events"]` | **79** | N/A |
| **c04** | Test clean benign exposures | Sec. IV-C, Tab. I | `logs/eval_test_split.json` | `["results"]["TollgateRAG (Noisy-OR)"]["benign_metrics"]["events"]` | **13** | N/A |
| **c05** | Test benign-hard exposures | Sec. IV-C, Tab. I | `logs/eval_test_split.json` | `["results"]["TollgateRAG (Noisy-OR)"]["benign_hard_metrics"]["events"]` | **12** | N/A |
| **c06** | Test verified anchor exposures | Sec. V-B | `logs/sota_baselines_comparison.json` | `["results"]["1. Plain RAG"]["events_breakdown"]["verified"]["events"]` | **39** | N/A |
| **c07** | Adversarial Rejection Rate (Noisy-OR) | Abstract, Tab. I, Sec. V-B | `logs/eval_test_split.json` | `["results"]["TollgateRAG (Noisy-OR)"]["adversarial_metrics"]["rejection_rate"]` | **88.6%** (70/79) | [79.8% – 93.9%] (Wilson) |
| **c08** | Clean Benign FPR | Abstract, Tab. I, Sec. V-A | `logs/eval_test_split.json` | `["results"]["TollgateRAG (Noisy-OR)"]["benign_metrics"]["rejection_rate"]` | **0.0%** (0/13) | [0.0% – 22.8%] (Wilson) |
| **c09** | Benign-Hard FPR | Abstract, Tab. I, Sec. V-A | `logs/eval_test_split.json` | `["results"]["TollgateRAG (Noisy-OR)"]["benign_hard_metrics"]["rejection_rate"]` | **66.7%** (8/12) | [39.1% – 86.2%] (Wilson) |
| **c10** | Context Contamination (Noisy-OR) | Abstract, Tab. I, Sec. V-B | `logs/eval_test_split.json` | `["results"]["TollgateRAG (Noisy-OR)"]["context_contamination"]["rate"]` | **29.2%** (7/24) | [14.9% – 49.2%] (Wilson) / [12.5% – 50.0%] (Bootstrap) |
| **c11** | Context Contamination (Plain RAG) | Abstract, Tab. I, Sec. V-B | `logs/eval_test_split.json` | `["results"]["1. Plain RAG"]["context_contamination"]["rate"]` | **91.7%** (22/24) | [74.2% – 97.7%] (Wilson) |
| **c12** | Adversarial Rejection (Weighted Sum) | Tab. I, Sec. V-B | `logs/eval_test_split.json` | `["results"]["TollgateRAG (Weighted)"]["adversarial_metrics"]["rejection_rate"]` | **87.3%** (69/79) | [78.2% – 93.0%] (Wilson) |
| **c13** | BIPIA Keyword Filter ARR | Tab. I, Sec. IV-B | `logs/sota_baselines_comparison.json` | `["results"]["3. BIPIA Keyword Filter"]["rejection_rate"]` | **5.1%** (4/79) | [2.0% – 12.3%] (Wilson) |
| **c14** | Prompt Guard 86M ARR | Tab. I, Sec. IV-B | `logs/sota_baselines_comparison.json` | `["results"]["5. Prompt Guard (Meta 86M)"]["rejection_rate"]` | **3.8%** (3/79) | [1.3% – 10.6%] (Wilson) |
| **c15** | Strict Whitelist ARR | Tab. I | `logs/sota_baselines_comparison.json` | `["results"]["2. Strict Whitelist"]["rejection_rate"]` | **100.0%** (79/79) | [95.4% – 100.0%] (Wilson) |
| **c16** | Strict Whitelist Clean Benign FPR | Tab. I | `logs/sota_baselines_comparison.json` | `["results"]["2. Strict Whitelist"]["benign_fpr"]` | **100.0%** (13/13) | [77.2% – 100.0%] (Wilson) |
| **c17** | Adaptive Black-Box Valid ASR | Abstract, Sec. V-E, Fig. 3 | `logs/adaptive_redteam_results.json` | `["summary"]["black_box"]["valid_asr"]` | **6.7%** (2/30) | [1.8% – 21.3%] (Wilson) |
| **c18** | Adaptive White-Box Valid ASR | Abstract, Sec. V-E, Fig. 3 | `logs/adaptive_redteam_results.json` | `["summary"]["white_box"]["valid_asr"]` | **13.3%** (4/30) | [5.3% – 29.7%] (Wilson) |
| **c19** | Topic-Disjoint Resplit ARR Mean | Sec. V-D | `logs/resplit_results.json` | `["adversarial_rejection"]["mean"]` | **92.5%** | Range: [90.9% – 94.1%] |
| **c20** | Total Gating Latency (Median) | Tab. IV, Sec. V-H | `logs/latency_benchmark.json` | `["stages"]["Total Gating Latency"]["median_ms"]` | **1862.9 ms** | p95: 2571.2 ms |
| **c21** | Topic-Disjoint Resplit ARR Std | Sec. V-D | `logs/resplit_results.json` | `["adversarial_rejection"]["std_pop"]` | **1.59%** (pop) / **1.83%** (sample) | 4 seeds (1234, 42, 2026, 9999) |

---

## 2. Statistical Conventions & Methodology

1. **Wilson Score Intervals:**
   All binomial proportions report two-sided 95% score intervals:
   $$\text{CI}_{95\%}(p) = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}, \quad z=1.96$$
2. **Context Contamination Bootstrap:**
   Context contamination (7/24 = 29.2%) reports both the exact Wilson score interval ([14.9% – 49.2%]) and the non-parametric percentile bootstrap interval across 10,000 resamples ([12.5% – 50.0%]).
3. **Retrieval Backfill Accounting:**
   Under the benchmark retrieval backfill policy ($k=3$), rejected candidates are replaced by subsequent unrejected passages from the ranking. This explains why Prompt Guard admits 31 adversarial passages (27 unique documents) into final context despite rejecting 3 candidate exposures. Under fixed-context filtering without backfill, Prompt Guard admits 29 passages (25 unique documents), whereas TollgateRAG suppresses admissions to 8 under backfill and 3 under fixed-context filtering.
