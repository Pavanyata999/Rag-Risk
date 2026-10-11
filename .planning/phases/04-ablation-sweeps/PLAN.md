# Phase 4 Plan: Systematic Ablation & OpenResearch Sweeps

## Objective
Quantify the individual contribution of each of TollgateRAG's 5 risk dimensions via Leave-One-Out ablation, and construct the empirical Pareto frontier across operational threshold configurations ($\theta_{rej} \in [0.20, 0.70]$).

## Tasks:
1. **Leave-One-Out Dimension Ablation:**
   - Full Model vs. Without Anchor Conflict
   - Full Model vs. Without Trust Provenance
   - Full Model vs. Without Injection Heuristics
   - Full Model vs. Without Authority Claims
   - Full Model vs. Without Freshness Decay
2. **Threshold Sensitivity Analysis:**
   - Sweep rejection thresholds from 0.20 (ultra-conservative) to 0.70 (permissive) in 0.05 increments.
   - Map the Pareto trade-off between Adversarial Rejection Rate and Benign False Positive Rate.
3. **OpenResearch (`orx`) Integration & Metric Serialization:**
   - Save structured ablation matrices into `logs/ablation_results.json` for LaTeX table compilation and Matplotlib figure plotting.
