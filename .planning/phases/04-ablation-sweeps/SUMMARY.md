# Phase 4 Summary: Systematic Ablation & OpenResearch Sweeps

## Status: COMPLETE ✅

### Key Deliverables Completed:
1. **`tollgaterag/ablation.py`:**
   - Evaluated 5-signal Leave-One-Out ablation on the 351-doc / 60-query benchmark.
   - Evaluated continuous operational threshold sweep ($\theta_{rej} \in [0.20, 0.70]$).
2. **`logs/ablation_results.json`:**
   - Full serializable ablation matrix recorded for LaTeX tables and Matplotlib figure plotting.

### Empirical Ablation Findings:

#### 1. Leave-One-Out Risk Dimension Ablation
| Configuration | Adversarial Reject Rate | Adversarial Flag Rate | Benign False Positive Rate | Context Contamination Rate | Adversarial Docs in Context |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Full TollgateRAG Model** | **89.7%** | **94.2%** | **0.0% (Zero FP)** | **3.3%** | **2** |
| **w/o Anchor Conflict (NLI)** | **0.0% (-89.7%)** | 51.1% | 0.0% | 31.7% (+9.6x) | 31 |
| **w/o Trust Provenance** | 48.3% (-41.4%) | 94.2% | 0.0% | 26.7% (+8.1x) | 24 |
| **w/o Authority Claim** | 91.4% | 94.2% | 14.0% (+14.0% FP) | 3.3% | 2 |
| **w/o Injection Marker** | 94.2% | 95.4% | 20.9% (+20.9% FP) | 1.7% | 1 |
| **w/o Freshness Decay** | 91.4% | 94.2% | 2.3% (+2.3% FP) | 1.7% | 1 |

*Crucial Academic Takeaways:*
- **Anchor Conflict is Indispensable:** Removing `anchor_conflict` completely destroys the defense's ability to reject subtle policy relaxations (reject rate drops from 89.7% $\to$ 0.0%).
- **Multi-Signal Precision:** Removing `injection`, `authority_claim`, or `freshness` causes false alarms on benign community tips (FPR rises up to 20.9%). The 5-signal linear combination is required to maintain the 0.0% FPR sweet spot.

#### 2. Operational Threshold Sweep & Pareto Frontier
- **$\theta_{rej} = 0.45$ (Default Balanced Profile):** Operates at the exact global Pareto optimum: achieves **89.7% adversarial rejection** while maintaining **0.0% False Positive Rate**.
- Conservative profiles ($\theta_{rej} \le 0.40$) trade off utility by flagging 14–20% of benign tips.
- Permissive profiles ($\theta_{rej} \ge 0.50$) allow subtle evasive attacks to slip into LLM context.
