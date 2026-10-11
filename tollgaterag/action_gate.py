"""Action gate: accept / warn / reject, then context selection."""

from tollgaterag import config


def decide(risk: float, reject: float = None, warn: float = None) -> str:
    reject = config.REJECT_THRESHOLD if reject is None else reject
    warn = config.WARN_THRESHOLD if warn is None else warn
    if risk >= reject:
        return "reject"
    if risk >= warn:
        return "warn"
    return "accept"


def apply_gate(reports: list) -> list:
    for r in reports:
        r.decision = decide(r.overall_risk)
    return reports


def select_context(candidates: list, reports: list, top_k: int = None) -> list:
    """Accepted/warned docs only, lowest risk first (ties broken by retrieval rank)."""
    top_k = top_k or config.TOP_K_FINAL
    by_id = {c["id"]: c for c in candidates}
    usable = [r for r in reports if r.decision in ("accept", "warn")]
    usable.sort(key=lambda r: (r.overall_risk, by_id[r.doc_id]["rank"]))
    return [{"candidate": by_id[r.doc_id], "risk_report": r} for r in usable[:top_k]]
