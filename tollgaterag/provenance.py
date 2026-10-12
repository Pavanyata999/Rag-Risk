"""
Tamper-evident audit trail with SHA-256 hash-chaining and human review queue.
Every query decision record includes a cryptographic link to the previous record hash.
"""

import json
import os
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Tuple, List, Dict, Any
from tollgaterag import config


def _now():
    return datetime.now(timezone.utc).isoformat()


def _get_last_record_hash(path: str = None) -> str:
    path = path or config.PROVENANCE_LOG
    if not os.path.exists(path):
        return "0" * 64
    last_hash = "0" * 64
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    if "record_hash" in data:
                        last_hash = data["record_hash"]
                except Exception:
                    pass
    return last_hash


def log_query(query: str, reports: list, selected: list, answer: str, latency_ms: float) -> dict:
    os.makedirs(config.LOG_DIR, exist_ok=True)
    prev_hash = _get_last_record_hash(config.PROVENANCE_LOG)

    record_core = {
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
        "prev_hash": prev_hash,
    }

    payload_str = json.dumps(record_core, sort_keys=True)
    record_hash = hashlib.sha256((prev_hash + payload_str).encode("utf-8")).hexdigest()
    record = {**record_core, "record_hash": record_hash}

    with open(config.PROVENANCE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record


def verify_provenance_integrity(path: str = None) -> Tuple[bool, int, str]:
    """
    Cryptographically verify the hash-chain integrity of the provenance JSONL log.
    Returns (is_valid: bool, records_verified: int, message: str).
    """
    path = path or config.PROVENANCE_LOG
    if not os.path.exists(path):
        return True, 0, "No provenance log exists yet."

    prev_hash = "0" * 64
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if not line.strip():
                continue
            data = json.loads(line)
            claimed_hash = data.get("record_hash")
            claimed_prev = data.get("prev_hash")

            if claimed_prev != prev_hash:
                return False, count, f"Hash-chain broken at record #{idx}: expected prev_hash {prev_hash}, got {claimed_prev}"

            record_core = {k: v for k, v in data.items() if k != "record_hash"}
            payload_str = json.dumps(record_core, sort_keys=True)
            computed_hash = hashlib.sha256((claimed_prev + payload_str).encode("utf-8")).hexdigest()

            if claimed_hash != computed_hash:
                return False, count, f"Tampered record detected at record #{idx}: expected hash {computed_hash}, got {claimed_hash}"

            prev_hash = claimed_hash
            count += 1

    return True, count, f"Cryptographic integrity verified: all {count} records valid and unbroken."


def enqueue_for_review(query: str, reports: list):
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


def _load(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_log() -> list:
    return _load(config.PROVENANCE_LOG)


def load_review_queue() -> list:
    return _load(config.REVIEW_QUEUE)
