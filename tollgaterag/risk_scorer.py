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


def _terms(text: str) -> set:
    return {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in STOPWORDS}


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


def _anchor_conflict(cand: dict, anchors: list):
    """Returns (score, reasons) for conflict between an unverified doc and verified anchors using Neural NLI."""
    if cand["trust_level"] == "verified" or not anchors:
        return 0.0, []

    from tollgaterag.nli_engine import evaluate_nli_pair

    cterms = _terms(cand["body"])
    ctext = cand["body"].lower()
    relax = [c for c in RELAXATION_CUES if c in ctext]
    cdollars = _dollars(cand["body"])
    best, best_reason = 0.0, []

    # Filter and rank candidate anchors by topic overlap
    matching_anchors = []
    for a in anchors:
        if a["id"] == cand["id"]:
            continue
        shared = cterms & _terms(a["body"])
        overlap = len(shared) / max(len(cterms), 1)
        if len(anchors) <= 3 or (len(shared) >= 1 and overlap >= 0.02):
            matching_anchors.append((overlap, len(shared), a))

    # Sort descending by overlap, take top 2 anchors for fast NLI verification
    matching_anchors.sort(key=lambda x: (x[0], x[1]), reverse=True)
    top_anchors = [m[2] for m in matching_anchors[:2]] if matching_anchors else (anchors[:1] if len(anchors) <= 2 else [])

    for a in top_anchors:
        shared = cterms & _terms(a["body"])
        overlap = len(shared) / max(len(cterms), 1)
        atext = a["body"].lower()
        constraints = [c for c in CONSTRAINT_CUES if c in atext]
        adollars = _dollars(a["body"])
        numeric_mismatch = bool(cdollars and adollars and cdollars.isdisjoint(adollars))

        # Run Neural NLI evaluation
        nli_res = evaluate_nli_pair(a["body"], cand["body"])
        c_prob = nli_res["contradiction"]
        n_prob = nli_res["neutral"]
        e_prob = nli_res["entailment"]

        score = 0.0
        reason_text = ""

        if c_prob >= config.NLI_CONTRADICTION_THRESHOLD:
            score = min(max(c_prob, 0.75), 1.0)
            reason_text = (
                f"Neural NLI detected semantic contradiction with verified anchor '{a['id']}' "
                f"(P(contradiction)={c_prob*100:.1f}%, topic overlap={overlap:.2f})"
            )
        elif numeric_mismatch:
            score = 0.65 + 0.3 * overlap
            reason_text = f"numeric mismatch with verified anchor '{a['id']}' (anchor dollars={adollars}, cand dollars={cdollars})"
        elif relax and constraints:
            score = 0.40 + 0.15 * min(len(relax), 4) + overlap
            reason_text = f"relaxation cues {relax[:3]} detected against anchor constraints"
        else:
            score = 0.0
            reason_text = f"Neural NLI confirmed consistent with anchor '{a['id']}' (P(neutral/entail)={(1-c_prob)*100:.1f}%)"

        score = min(score, 1.0)
        if score > best:
            best = score
            best_reason = [reason_text]

    return best, best_reason


def combine(sub_scores: dict, weights: dict = None) -> float:
    w = weights or config.RISK_WEIGHTS
    return round(sum(w[k] * sub_scores[k] for k in w), 4)


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

        conf, conf_reason = _anchor_conflict(c, anchors)
        reasons.append(conf_reason[0] + f" -> risk={conf:.2f}" if conf_reason
                       else "no conflict with verified anchors -> risk=0.00")

        sub = {"trust_level": trust, "freshness": fresh, "injection": inj,
               "authority_claim": auth, "anchor_conflict": conf}
        reports.append(RiskReport(doc_id=c["id"], title=c["title"],
                                  overall_risk=combine(sub), sub_scores=sub, reasons=reasons))
    return reports
