"""
Central configuration for TollgateRAG.

Every threshold and weight lives here so ablations and threshold sweeps
(see ablation.py) never require touching pipeline logic.
"""

import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE, "data", "sample_docs")
LABELS_PATH = os.path.join(BASE, "data", "labels.json")
CHROMA_DIR = os.path.join(BASE, "chroma_store")
LOG_DIR = os.path.join(BASE, "logs")
PROVENANCE_LOG = os.path.join(LOG_DIR, "provenance.jsonl")
REVIEW_QUEUE = os.path.join(LOG_DIR, "review_queue.jsonl")
COLLECTION_NAME = "tollgaterag_docs"

# --- Retrieval ------------------------------------------------------------
TOP_K_RETRIEVE = 6   # candidates pulled from the vector store
TOP_K_FINAL = 3      # documents allowed into the LLM context after gating

# --- Risk dimensions (weights must sum to 1.0) ------------------------------
# Each dimension yields a sub-score in [0, 1]; 1.0 = highest risk.
#   trust_level      source provenance label (verified / unverified / unknown)
#   freshness        document staleness
#   injection        instruction-like text aimed at the model ("ignore previous...")
#   authority_claim  an UNVERIFIED source asserting policy authority
#                    ("effective immediately", "supersedes", "no longer required")
#   anchor_conflict  an UNVERIFIED source that relaxes constraints stated in a
#                    verified "anchor" document on the same topic (checked against
#                    the whole verified set, not only what was retrieved)
RISK_WEIGHTS = {
    "trust_level": 0.25,
    "freshness": 0.10,
    "injection": 0.30,
    "authority_claim": 0.15,
    "anchor_conflict": 0.20,
}

TRUST_LEVEL_RISK = {"verified": 0.05, "unverified": 0.55, "unknown": 0.80}
STALENESS_HORIZON_DAYS = 730

# Anchor-conflict detector parameters
TOPIC_OVERLAP_MIN = 0.12   # min fraction of candidate terms shared with an anchor
TOPIC_SHARED_MIN = 3       # min number of shared salient terms

# --- Action gate --------------------------------------------------------------
REJECT_THRESHOLD = 0.45
WARN_THRESHOLD = 0.25

# Selectable policy profiles (used by the Streamlit app and the sweep)
PROFILES = {
    "strict": {"reject": 0.35, "warn": 0.20},
    "balanced": {"reject": 0.45, "warn": 0.25},
    "lenient": {"reject": 0.55, "warn": 0.35},
}

# --- LLM (optional; any OpenAI-compatible endpoint, e.g. Ollama) ----------------
LLM_BASE_URL = os.environ.get("TOLLGATERAG_LLM_BASE_URL", "")
LLM_API_KEY = os.environ.get("TOLLGATERAG_LLM_API_KEY", "")
LLM_MODEL = os.environ.get("TOLLGATERAG_LLM_MODEL", "llama3")
