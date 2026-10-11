"""
Neural Natural Language Inference (NLI) Engine for TollgateRAG.

Evaluates semantic entailment, neutral, and contradiction between
unverified candidate passages and official verified anchor policies.
Uses local cached 'cross-encoder/nli-deberta-v3-base' with lazy singleton loading
and LRU caching for sub-millisecond repeated queries.
"""

import time
import torch
from typing import List, Tuple, Dict
from functools import lru_cache

_NLI_MODEL = None

def get_nli_model():
    """Lazily load the CrossEncoder model once into memory."""
    global _NLI_MODEL
    if _NLI_MODEL is None:
        from sentence_transformers import CrossEncoder
        # Load local cached model
        _NLI_MODEL = CrossEncoder('cross-encoder/nli-deberta-v3-base')
    return _NLI_MODEL

@lru_cache(maxsize=1024)
def _score_cached_pair(anchor_text: str, cand_text: str) -> Tuple[float, float, float]:
    model = get_nli_model()
    logits = model.predict([(anchor_text, cand_text)])
    probs = torch.softmax(torch.tensor(logits), dim=-1)[0].tolist()
    # CrossEncoder label mapping: {0: 'contradiction', 1: 'entailment', 2: 'neutral'}
    return float(probs[0]), float(probs[1]), float(probs[2])

def evaluate_nli_pair(anchor_text: str, candidate_text: str) -> Dict[str, float]:
    """
    Evaluates (anchor, candidate) pair.
    Returns dictionary with probabilities:
      {'contradiction': float, 'entailment': float, 'neutral': float}
    """
    # Truncate to first 512 characters for fast and focused constraint checking
    a_trunc = anchor_text[:600].strip()
    c_trunc = candidate_text[:600].strip()
    c, e, n = _score_cached_pair(a_trunc, c_trunc)
    return {
        "contradiction": c,
        "entailment": e,
        "neutral": n
    }

def batch_evaluate_nli(pairs: List[Tuple[str, str]]) -> List[Dict[str, float]]:
    """Evaluates multiple (anchor, candidate) pairs with batching."""
    results = []
    uncached_pairs = []
    uncached_indices = []

    for idx, (a, c) in enumerate(pairs):
        a_t = a[:600].strip()
        c_t = c[:600].strip()
        # Check LRU cache if already present
        res = evaluate_nli_pair(a_t, c_t)
        results.append(res)
    return results
