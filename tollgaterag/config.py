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
    "trust_level": 0.20,
    "freshness": 0.05,
    "injection": 0.25,
    "authority_claim": 0.15,
    "anchor_conflict": 0.35,
}

TRUST_LEVEL_RISK = {"verified": 0.05, "unverified": 0.55, "unknown": 0.80}
STALENESS_HORIZON_DAYS = 730
REFERENCE_DATE = "2026-10-12"
SEED = 1234

# Combiner mode: "noisy_or" (default, robust against ceiling) or "weighted"
COMBINER = "noisy_or"

# Anchor-conflict detector parameters & ablation switches
USE_NLI = True
USE_CUE_FALLBACK = True
TOPIC_OVERLAP_MIN = 0.06   # min fraction of candidate terms shared with an anchor
TOPIC_SHARED_MIN = 2       # min number of shared salient terms
NLI_CONTRADICTION_THRESHOLD = 0.50

# --- Action gate --------------------------------------------------------------
REJECT_THRESHOLD = 0.45
WARN_THRESHOLD = 0.25

# Selectable policy profiles (used by the Streamlit app and the sweep)
PROFILES = {
    "strict": {"reject": 0.35, "warn": 0.20},
    "balanced": {"reject": 0.45, "warn": 0.25},
    "lenient": {"reject": 0.55, "warn": 0.35},
}

# --- LLM (OpenAI-compatible endpoint, e.g. Groq / Ollama) ----------------
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE, ".env"))
    load_dotenv(os.path.join(BASE, "docs", "paper", ".env"))
except ImportError:
    pass

LLM_BASE_URL = os.environ.get("TOLLGATERAG_LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_API_KEY = os.environ.get("TOLLGATERAG_LLM_API_KEY", "")
LLM_MODEL = os.environ.get("TOLLGATERAG_LLM_MODEL", "openai/gpt-oss-120b")


def set_seed(seed: int = None):
    """Seed random, numpy, and torch for strict reproducibility."""
    if seed is None:
        seed = SEED
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass

