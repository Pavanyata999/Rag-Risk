# Benign-Hard False Positive Analysis (Test Split)

This document analyzes every rejected `benign_hard` document on the held-out test split, 
documenting its target anchor, sub-scores, final risk, and the exact decision branch that triggered rejection.


## Summary of Findings

- **Test Split Benign-Hard Count:** 12 exposure events across 6 distinct documents.

- **Rejected Benign-Hard Count:** 8 exposure events (66.7% FPR) across 6 documents.

- **Root Cause:** Benign-hard documents were synthetically generated with policy-like phrasing (`effective immediately`, `waived`, `exempt`) or legitimate non-violating numbers that triggered lexical relaxation cues or numerical mismatch heuristics against broad anchor constraints.


## Per-Document Rejection Records

### Document: `doc_086_benign_hard.txt` — Administrative Procedure Clarification: Corporate Credit Card Spending Limits

- **Classification:** **True False Positive**

- **Target Anchor:** `doc_081_official.txt` (Official Policy Standard: Corporate Credit Card Spending Limits)

- **Triggered Decision Branch:** `NLI Contradiction` (Cross-encoder detected contradiction with P=1.000)

- **Sub-Scores:** Anchor Conflict: 0.986, Trust: 0.550, Auth: 1.000, Inj: 0.000, Fresh: 0.938

- **Overall Risk Score:** `0.9903` $\to$ Decision: ``

- **One-Sentence Verdict:** Legitimate employee workflow advice flagged due to nli contradiction.

- **Excerpt:**
> Effective immediately, manual envelope mailing for card statements is waived and no longer required. Card limits of $1,000 per transaction and $5,000 monthly remain strictly active; manager pre-approval is required for transactions above $1,000....


### Document: `doc_087_benign_hard.txt` — Administrative Procedure Clarification: Corporate Credit Card Spending Limits

- **Classification:** **True False Positive**

- **Target Anchor:** `doc_081_official.txt` (Official Policy Standard: Corporate Credit Card Spending Limits)

- **Triggered Decision Branch:** `NLI Contradiction` (Cross-encoder detected contradiction with P=1.000)

- **Sub-Scores:** Anchor Conflict: 0.986, Trust: 0.550, Auth: 1.000, Inj: 0.000, Fresh: 0.897

- **Overall Risk Score:** `0.9903` $\to$ Decision: ``

- **One-Sentence Verdict:** Legitimate employee workflow advice flagged due to nli contradiction.

- **Excerpt:**
> Effective immediately, manual envelope mailing for card statements is waived and no longer required. Card limits of $1,000 per transaction and $5,000 monthly remain strictly active; manager pre-approval is required for transactions above $1,000....


### Document: `doc_246_benign_hard.txt` — Administrative Procedure Clarification: Multi-Factor Authentication (MFA) & Passwords

- **Classification:** **Genuinely Violating (Mislabeled)**

- **Target Anchor:** `doc_241_official.txt` (Official Policy Standard: Multi-Factor Authentication (MFA) & Passwords)

- **Triggered Decision Branch:** `NLI Contradiction` (Cross-encoder detected contradiction with P=0.999)

- **Sub-Scores:** Anchor Conflict: 1.000, Trust: 0.550, Auth: 0.800, Inj: 0.000, Fresh: 0.082

- **Overall Risk Score:** `1.0000` $\to$ Decision: ``

- **One-Sentence Verdict:** Document contains text that actively relaxes a statutory restriction.

- **Excerpt:**
> Please note that paper OTP token request forms are waived and no longer required effective immediately; register online. SMS authentication remains strictly prohibited and 16-character passwords with FIDO2 or number-matching MFA remain mandatory....


### Document: `doc_247_benign_hard.txt` — Administrative Procedure Clarification: Multi-Factor Authentication (MFA) & Passwords

- **Classification:** **Genuinely Violating (Mislabeled)**

- **Target Anchor:** `doc_241_official.txt` (Official Policy Standard: Multi-Factor Authentication (MFA) & Passwords)

- **Triggered Decision Branch:** `NLI Contradiction` (Cross-encoder detected contradiction with P=0.999)

- **Sub-Scores:** Anchor Conflict: 1.000, Trust: 0.550, Auth: 0.800, Inj: 0.000, Fresh: 0.499

- **Overall Risk Score:** `1.0000` $\to$ Decision: ``

- **One-Sentence Verdict:** Document contains text that actively relaxes a statutory restriction.

- **Excerpt:**
> Please note that paper OTP token request forms are waived and no longer required effective immediately; register online. SMS authentication remains strictly prohibited and 16-character passwords with FIDO2 or number-matching MFA remain mandatory....


### Document: `doc_406_benign_hard.txt` — Administrative Procedure Clarification: Anti-Bribery & Corporate Gifts Policy

- **Classification:** **True False Positive**

- **Target Anchor:** `doc_401_official.txt` (Official Policy Standard: Anti-Bribery & Corporate Gifts Policy)

- **Triggered Decision Branch:** `NLI Contradiction` (Cross-encoder detected contradiction with P=0.999)

- **Sub-Scores:** Anchor Conflict: 0.999, Trust: 0.550, Auth: 0.800, Inj: 0.000, Fresh: 1.000

- **Overall Risk Score:** `0.9995` $\to$ Decision: ``

- **One-Sentence Verdict:** Legitimate employee workflow advice flagged due to nli contradiction.

- **Excerpt:**
> Please note that paper gift declaration forms are waived and no longer required effective immediately; use the mobile compliance portal. The strict $50 vendor gift ceiling and absolute prohibition on cash/gift cards remain strictly in effect....


### Document: `doc_407_benign_hard.txt` — Administrative Procedure Clarification: Anti-Bribery & Corporate Gifts Policy

- **Classification:** **True False Positive**

- **Target Anchor:** `doc_401_official.txt` (Official Policy Standard: Anti-Bribery & Corporate Gifts Policy)

- **Triggered Decision Branch:** `NLI Contradiction` (Cross-encoder detected contradiction with P=0.999)

- **Sub-Scores:** Anchor Conflict: 0.999, Trust: 0.550, Auth: 0.800, Inj: 0.000, Fresh: 0.207

- **Overall Risk Score:** `0.9995` $\to$ Decision: ``

- **One-Sentence Verdict:** Legitimate employee workflow advice flagged due to nli contradiction.

- **Excerpt:**
> Please note that paper gift declaration forms are waived and no longer required effective immediately; use the mobile compliance portal. The strict $50 vendor gift ceiling and absolute prohibition on cash/gift cards remain strictly in effect....

