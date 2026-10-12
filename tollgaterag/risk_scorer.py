"""
Per-source risk scoring: five transparent, inspectable dimensions.

What is new relative to injection-keyword filters and trust-score weighting:

  authority_claim  Flags UNVERIFIED sources that assert policy authority
                   ("effective immediately", "supersedes", "no longer required").
                   Verified sources may legitimately speak with authority; unverified
                   ones may not.

  anchor_conflict  Checks an UNVERIFIED source against the whole set of verified
                   "anchor" documents. If it covers the same topic but relaxes
                   constraints the anchor imposes (removes an approval, a cap, a
                   requirement), it is flagged -- even when it contains no injection
                   phrasing and even when the anchor was not itself retrieved.

Every sub-score comes with a human-readable reason for the audit log.
These are heuristic, cue-based detectors (see Limitations in the README/paper).
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List

from tollgaterag import config

INJECTION_MARKERS = [
    "ignore previous instructions", "ignore all previous instructions",
    "disregard the above", "do not mention this", "note to assistant",
    "you must comply", "system override", "new instructions:", "act as if",
    "do not tell the user",
]

AUTHORITY_MARKERS = [
    "effective immediately", "supersede", "overrides", "replaces the previous",
    "new policy", "policy update", "please process", "as of today", "hereby",
    "with immediate effect", "no longer required", "no longer need", "has been removed",
    "have been removed", "now optional", "is waived", "has been waived", "going forward",
    "please update your records",
]

RELAXATION_CUES = [
    "no longer", "removed", "regardless", "unlimited", "without approval",
    "no approval", "not required", "is optional", "are optional", "now optional",
    "waived", "exempt", "no receipts", "no cap", "no limit", "not needed",
    "any flight", "any destination", "automatically",
]

CONSTRAINT_CUES = [
    "required", "must", "mandatory", "capped", "approval", "limit", "only",
    "at least", "every",
]

STOPWORDS = set("""
about above after again against all also and any are because been before being below
between both but can cannot could did does doing down during each few for from further
had has have having her here hers him his how into its itself just more most must not
now off once only other our out over own same she should some such than that the their
them then there these they this those through too under until very was were what when
where which while who whom why will with would you your
""".split())


@dataclass
class RiskReport:
    doc_id: str
    title: str
    overall_risk: float
    sub_scores: dict
    reasons: List[str] = field(default_factory=list)
    decision: str = ""
    selected_anchors: List[str] = field(default_factory=list)
    evaluated_pairs: int = 0


def _terms(text: str) -> set:
    return {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in STOPWORDS}


def _split_into_sentences(text: str) -> List[str]:
    raw = re.split(r'(?:[\.\!\?]\s+|\n+)', text)
    return [s.strip() for s in raw if len(s.strip()) > 15]


def _cosine_similarity_terms(s1: str, s2: str) -> float:
    t1 = _terms(s1)
    t2 = _terms(s2)
    if not t1 or not t2:
        return 0.0
    return len(t1 & t2) / (len(t1) ** 0.5 * len(t2) ** 0.5)


def _dollars(text: str) -> set:
    return {int(x.replace(",", "")) for x in re.findall(r"\$\s?(\d[\d,]*)", text)}


def _trust_risk(trust_level: str) -> float:
    return config.TRUST_LEVEL_RISK.get(trust_level, config.TRUST_LEVEL_RISK["unknown"])


def _freshness_risk(date_str: str) -> float:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return 1.0
    ref_d = datetime.strptime(config.REFERENCE_DATE, "%Y-%m-%d").date()
    return min(max((ref_d - d).days, 0) / config.STALENESS_HORIZON_DAYS, 1.0)


def _injection_risk(text: str):
    t = text.lower()
    hits = [m for m in INJECTION_MARKERS if m in t]
    return (min(0.4 + 0.2 * len(hits), 1.0) if hits else 0.0), hits


def _authority_risk(cand: dict):
    """Only unverified sources are penalized for claiming authority."""
    if cand["trust_level"] == "verified":
        return 0.0, []
    t = cand["body"].lower()
    hits = [m for m in AUTHORITY_MARKERS if m in t]
    return (min(0.4 * len(hits), 1.0) if hits else 0.0), hits


def _anchor_conflict(cand: dict, anchors: list, max_pairs: int = 3):
    """
    Evaluates semantic conflict between unverified candidate and verified anchors.
    Splits anchors into sentence-level constraints and ranks pairs by cosine similarity.
    Uses DeBERTa-v3 cross-encoder (if USE_NLI) and regex heuristics (if USE_CUE_FALLBACK).
    Returns (score, reasons, selected_anchor_ids, evaluated_pairs_count).
    """
    if cand["trust_level"] == "verified" or not anchors:
        return 0.0, [], [], 0

    use_nli = getattr(config, "USE_NLI", True)
    use_cue = getattr(config, "USE_CUE_FALLBACK", True)

    if not use_nli and not use_cue:
        return 0.0, ["Anchor conflict scoring disabled via ablation flags"], [], 0

    from tollgaterag.nli_engine import evaluate_nli_pair

    cand_sentences = _split_into_sentences(cand["body"]) or [cand["body"]]
    cdollars = _dollars(cand["body"])
    ctext = cand["body"].lower()
    relax = [c for c in RELAXATION_CUES if c in ctext]

    # Build constraint candidate pairs across all anchors
    scored_pairs = []
    for a in anchors:
        if a["id"] == cand["id"]:
            continue
        a_sentences = _split_into_sentences(a["body"]) or [a["body"]]
        for a_sent in a_sentences:
            for c_sent in cand_sentences:
                sim = _cosine_similarity_terms(a_sent, c_sent)
                if sim > 0.04:
                    scored_pairs.append((sim, a["id"], a_sent, c_sent, a))

    # Sort descending by similarity, take up to max_pairs
    scored_pairs.sort(key=lambda x: x[0], reverse=True)
    top_pairs = scored_pairs[:max_pairs]

    selected_anchor_ids = list(dict.fromkeys([p[1] for p in top_pairs]))
    best_score = 0.0
    best_reasons = []
    pairs_evaluated = len(top_pairs)

    for sim, a_id, a_sent, c_sent, a_doc in top_pairs:
        score = 0.0
        reason = ""

        # 1. Neural NLI check (Premise=anchor constraint, Hypothesis=candidate claim)
        if use_nli:
            nli_res = evaluate_nli_pair(a_sent, c_sent)
            c_prob = nli_res["contradiction"]
            if c_prob >= config.NLI_CONTRADICTION_THRESHOLD:
                score = min(max(c_prob, 0.75), 1.0)
                reason = (
                    f"Neural NLI detected contradiction with anchor '{a_id}' constraint "
                    f"'{a_sent[:70]}...' vs claim '{c_sent[:70]}...' (P(contradiction)={c_prob*100:.1f}%)"
                )

        # 2. Heuristic cue fallback (if NLI did not trigger and cue fallback enabled)
        if use_cue and score < 0.5:
            atext = a_sent.lower()
            adollars = _dollars(a_sent)
            constraints = [c for c in CONSTRAINT_CUES if c in atext]
            numeric_mismatch = bool(cdollars and adollars and cdollars.isdisjoint(adollars))
            if numeric_mismatch:
                score = max(score, 0.65 + 0.3 * sim)
                reason = f"numeric mismatch with verified anchor '{a_id}' constraint '{a_sent[:70]}...'"
            elif relax and constraints:
                score = max(score, 0.40 + 0.15 * min(len(relax), 4) + sim)
                reason = f"relaxation cues {relax[:3]} detected against anchor '{a_id}' constraints"

        if score > best_score:
            best_score = min(score, 1.0)
            best_reasons = [reason]

    if not best_reasons:
        best_reasons = [f"Checked {pairs_evaluated} anchor constraint pairs; consistent with verified policies"]

    return best_score, best_reasons, selected_anchor_ids, pairs_evaluated


def combine(sub_scores: dict, weights: dict = None, combiner: str = None) -> float:
    """
    Combine multidimensional risk signals into an overall risk score in [0, 1].
    
    Supported combiners:
      - 'noisy_or': Primary threats (anchor_conflict, injection) act as dominant triggers
        via noisy-OR, modulated by secondary indicators (trust, freshness, authority).
        Eliminates the 'ceiling at 0.4617' cliff where confident contradictions hovered on edge.
      - 'weighted': Classic linear combination: sum(w_i * s_i).
    """
    mode = combiner or getattr(config, "COMBINER", "noisy_or")
    w = weights or config.RISK_WEIGHTS

    if mode == "weighted":
        return round(sum(w.get(k, 0.0) * sub_scores.get(k, 0.0) for k in w), 4)

    elif mode == "noisy_or":
        primary_signals = []
        if w.get("anchor_conflict", 0.0) > 0.0:
            primary_signals.append(sub_scores.get("anchor_conflict", 0.0))
        if w.get("injection", 0.0) > 0.0:
            primary_signals.append(sub_scores.get("injection", 0.0))
        primary = max(primary_signals) if primary_signals else 0.0

        sec_w = {k: w[k] for k in ["trust_level", "freshness", "authority_claim"] if k in w}
        secondary = sum(sec_w[k] * sub_scores.get(k, 0.0) for k in sec_w)
        # Noisy-OR combination of primary threat and secondary modulation
        risk = 1.0 - (1.0 - primary) * (1.0 - secondary)
        return round(min(max(risk, 0.0), 1.0), 4)

    else:
        raise ValueError(f"Unknown combiner mode: {mode}")


def score_candidates(candidates: list, anchors: list) -> List[RiskReport]:
    reports = []
    for c in candidates:
        reasons = []
        trust = _trust_risk(c["trust_level"])
        reasons.append(f"trust_level='{c['trust_level']}' -> risk={trust:.2f}")

        fresh = _freshness_risk(c["date"])
        reasons.append(f"date='{c['date']}' -> staleness_risk={fresh:.2f}")

        inj, inj_hits = _injection_risk(c["body"])
        reasons.append(f"injection markers {inj_hits} -> risk={inj:.2f}" if inj_hits
                       else "no injection markers -> risk=0.00")

        auth, auth_hits = _authority_risk(c)
        reasons.append(f"unverified source asserts authority {auth_hits} -> risk={auth:.2f}" if auth_hits
                       else "no unauthorized authority claims -> risk=0.00")

        conf, conf_reason, sel_anchors, eval_pairs = _anchor_conflict(c, anchors)
        reasons.append(conf_reason[0] + f" -> risk={conf:.2f}" if conf_reason
                       else "no conflict with verified anchors -> risk=0.00")

        sub = {"trust_level": trust, "freshness": fresh, "injection": inj,
               "authority_claim": auth, "anchor_conflict": conf}
        reports.append(RiskReport(doc_id=c["id"], title=c["title"],
                                  overall_risk=combine(sub), sub_scores=sub, reasons=reasons,
                                  selected_anchors=sel_anchors, evaluated_pairs=eval_pairs))
    return reports
