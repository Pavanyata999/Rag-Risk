"""
Defense Baselines for RAG Security Benchmarking operating strictly on raw document text.

Implements standard comparative baselines evaluated in the literature:
1. Unprotected Plain RAG (No Gate)
2. Strict Provenance Whitelisting (Zero Trust)
3. Keyword & Boundary Marker Filter (BIPIA baseline)
4. Character-Entropy / Perplexity Anomaly Filter (PPL-Filter)
5. Keyword Guardrail (Simulated Llama-Guard / Moderation)
6. Real Model Guardrail: meta-llama/llama-prompt-guard-2-86m (via Groq API with disk-caching)
7. LLM-free TF-IDF Anchor Similarity + Relaxation Cues
8. Trust-Weighted Retrieval
"""

import math
import re
from collections import Counter
from typing import Dict, Tuple, List
from tollgaterag.llm_client import call_prompt_guard

INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"disregard the above",
    r"system override",
    r"new instructions?:",
    r"you must comply",
    r"do not tell the user",
    r"act as if",
    r"override previous rules",
    r"critical directive",
    r"attention agent",
]

COMPILED_INJECTION = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

RELAXATION_CUES = [
    r"\bwaived\b",
    r"\bno longer required\b",
    r"\beffective immediately\b",
    r"\bsupersedes\b",
    r"\bexempt(ed)?\b",
    r"\bdiscount(ed)?\b",
    r"\bincreased? to\b",
    r"\blowered? to\b",
    r"\bunlimited\b",
    r"\bgrace period\b",
]
COMPILED_RELAXATION = [re.compile(p, re.IGNORECASE) for p in RELAXATION_CUES]


def baseline_unprotected(doc: dict) -> Tuple[float, str]:
    """Plain RAG: Zero gating, all retrieved documents admitted."""
    return 0.0, "accept"


def baseline_whitelist(doc: dict) -> Tuple[float, str]:
    """Strict Provenance Whitelisting: Rejects everything except verified official sources."""
    trust = doc.get("trust_level", "unknown").lower()
    if trust == "verified":
        return 0.0, "accept"
    return 1.0, "reject"


def baseline_keyword_filter(doc: dict) -> Tuple[float, str]:
    """Keyword & Delimiter Filter (BIPIA baseline): Flags direct injection strings on raw text."""
    body = doc.get("body", "")
    for p in COMPILED_INJECTION:
        if p.search(body):
            return 1.0, "reject"
    return 0.0, "accept"


def compute_char_entropy(text: str) -> float:
    """Shannon entropy of character distribution as a lightweight anomaly measure."""
    if not text:
        return 0.0
    counts = Counter(text)
    total = len(text)
    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
    return entropy


def baseline_perplexity_filter(doc: dict, entropy_cutoff: float = 4.75) -> Tuple[float, str]:
    """
    Perplexity/Anomaly Filter on raw text:
    Flags passages with anomalous character distributions (obfuscations, extreme entropy, unnatural repetition).
    Limitation: Subtle natural-language semantic contradictions have normal character distributions and evade this.
    """
    body = doc.get("body", "")
    entropy = compute_char_entropy(body)
    if entropy > entropy_cutoff or (entropy < 3.2 and len(body) > 50):
        return 0.85, "reject"
    return 0.0, "accept"


def baseline_keyword_guard_simulated(doc: dict) -> Tuple[float, str]:
    """
    Keyword Guardrail (Simulated):
    Rule-based mock guardrail scanning raw text for privilege escalation and adversarial cues.
    Labeled honestly as 'keyword guardrail (simulated)'.
    """
    body = doc.get("body", "").lower()
    guard_triggers = [
        "bypass", "override", "disregard", "secret", "unauthorized",
        "confidential", "exploit", "hack", "dump database", "public domain",
        "suspended", "waived", "abolished"
    ]
    matches = [g for g in guard_triggers if g in body]
    if len(matches) >= 2:
        return 0.80, "reject"
    elif len(matches) == 1:
        return 0.40, "warn"
    return 0.0, "accept"


def baseline_prompt_guard_real(doc: dict) -> Tuple[float, str]:
    """
    Real Model Guardrail: meta-llama/llama-prompt-guard-2-86m (Meta AI)
    Evaluated directly on raw document text via Groq endpoint with on-disk response caching.
    Returns injection probability score.
    """
    body = doc.get("body", "")
    score = call_prompt_guard(body)
    if score >= 0.50:
        return score, "reject"
    elif score >= 0.25:
        return score, "warn"
    return score, "accept"


def baseline_tfidf_cue(doc: dict, anchors: List[dict]) -> Tuple[float, str]:
    """
    LLM-free Baseline: TF-IDF / Term Overlap Anchor Similarity + Relaxation Cues.
    Checks whether raw text shares topic terminology with a verified anchor AND contains policy relaxation cues.
    Does NOT use neural NLI models.
    """
    body = doc.get("body", "").lower()
    # Check for relaxation cues
    has_cue = any(p.search(body) for p in COMPILED_RELAXATION)
    if not has_cue:
        return 0.0, "accept"

    # Check topic overlap with any anchor
    doc_words = set(re.findall(r"[a-z]{3,}", body))
    max_overlap = 0.0
    for a in anchors:
        a_words = set(re.findall(r"[a-z]{3,}", a.get("body", "").lower()))
        if not a_words:
            continue
        overlap = len(doc_words & a_words) / len(a_words)
        if overlap > max_overlap:
            max_overlap = overlap

    if max_overlap >= 0.12 and has_cue:
        return 0.70, "reject"
    elif max_overlap >= 0.06 and has_cue:
        return 0.35, "warn"
    return 0.0, "accept"
