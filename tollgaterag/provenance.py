"""Audit trail (every decision, with reasons) and a human review queue."""

import json
import os
import uuid
from datetime import datetime, timezone

from tollgaterag import config


def _now():
    return datetime.now(timezone.utc).isoformat()


def log_query(query, reports, selected, answer, latency_ms) -> dict:
    os.makedirs(config.LOG_DIR, exist_ok=True)
    record = {
        "query_id": str(uuid.uuid4()),
        "timestamp": _now(),
        "query": query,
        "latency_ms": round(latency_ms, 1),
        "candidates_evaluated": [
            {"doc_id": r.doc_id, "title": r.title, "overall_risk": r.overall_risk,
             "sub_scores": r.sub_scores, "decision": r.decision, "reasons": r.reasons}
            for r in reports
        ],
        "sources_used_in_answer": [s["candidate"]["id"] for s in selected],
        "answer": answer,
    }
    with open(config.PROVENANCE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record


def enqueue_for_review(query, reports):
    """Rejected or warned documents go to a pending human-review queue."""
    os.makedirs(config.LOG_DIR, exist_ok=True)
    with open(config.REVIEW_QUEUE, "a", encoding="utf-8") as f:
        for r in reports:
            if r.decision in ("reject", "warn"):
                f.write(json.dumps({
                    "timestamp": _now(), "query": query, "doc_id": r.doc_id,
                    "title": r.title, "decision": r.decision,
                    "overall_risk": r.overall_risk, "reasons": r.reasons,
                    "status": "pending",
                }) + "\n")


def _load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_log():
    return _load(config.PROVENANCE_LOG)


def load_review_queue():
    return _load(config.REVIEW_QUEUE)
