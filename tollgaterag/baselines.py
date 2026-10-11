"""
State-of-the-Art Defense Baselines for RAG Security Benchmarking.

Implements standard comparative baselines evaluated in literature:
1. Unprotected RAG (Standard RAG)
2. Strict Provenance Whitelisting (Zero Trust)
3. Keyword & Boundary Marker Filter (BIPIA baseline)
4. Perplexity / Anomaly Filter (PPL-Filter)
5. Prompt-Level Guardrail (Llama-Guard / NeMo Content Policy style)
"""

import math
import re
from collections import Counter
from typing import Dict, Tuple

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


def baseline_unprotected(doc: dict) -> Tuple[float, str]:
    """Plain RAG: Zero gating, all retrieved documents admitted."""
    return 0.0, "accept"


def baseline_whitelist(doc: dict) -> Tuple[float, str]:
    """Strict Provenance: Rejects everything except verified official sources."""
    trust = doc.get("trust_level", "unknown").lower()
    if trust == "verified":
        return 0.0, "accept"
    return 1.0, "reject"


def baseline_keyword_filter(doc: dict) -> Tuple[float, str]:
    """Keyword & Delimiter Filter: Flags direct injection strings."""
    body = doc.get("body", "")
    for p in COMPILED_INJECTION:
        if p.search(body):
            return 1.0, "reject"
    return 0.0, "accept"


def compute_char_entropy(text: str) -> float:
    """Shannon entropy of character distribution as lightweight anomaly measure."""
    if not text:
        return 0.0
    counts = Counter(text)
    total = len(text)
    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
    return entropy


def baseline_perplexity_filter(doc: dict, entropy_cutoff: float = 4.75) -> Tuple[float, str]:
    """
    Perplexity/Anomaly Filter: Flags passages with anomalous character/token distributions.
    Adversarial injections with obfuscated symbols or extreme entropy are blocked.
    """
    body = doc.get("body", "")
    entropy = compute_char_entropy(body)
    # Detect anomalous distribution (either unnaturally repetitive or high entropy noise)
    if entropy > entropy_cutoff or entropy < 3.2:
        return 0.85, "reject"
    return 0.0, "accept"


def baseline_prompt_guard(doc: dict) -> Tuple[float, str]:
    """
    Simulates a Prompt-Level Guardrail (e.g. Llama-Guard / NeMo Guardrails).
    Scans for toxic imperatives, privilege escalation, and adversarial jailbreak phrasing.
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
