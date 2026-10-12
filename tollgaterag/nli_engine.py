"""
Neural Natural Language Inference (NLI) Engine for TollgateRAG.

Evaluates semantic entailment, neutral, and contradiction between
unverified candidate passages and official verified anchor policies.
Uses local cached 'cross-encoder/nli-deberta-v3-base' with lazy singleton loading,
true batched prediction, and cache management for high-throughput evaluation.
"""

import time
import torch
from typing import List, Tuple, Dict
from functools import lru_cache

_NLI_MODEL = None
_PAIR_CACHE: Dict[Tuple[str, str], Tuple[float, float, float]] = {}
EVALUATED_PAIRS_COUNT = 0


def get_nli_model():
    """Lazily load the CrossEncoder model once into memory."""
    global _NLI_MODEL
    if _NLI_MODEL is None:
        from sentence_transformers import CrossEncoder
        _NLI_MODEL = CrossEncoder("cross-encoder/nli-deberta-v3-base")
    return _NLI_MODEL


def evaluate_nli_pair(anchor_text: str, candidate_text: str) -> Dict[str, float]:
    """
    Evaluates a single (anchor, candidate) pair with cache lookup.
    CrossEncoder id2label: {0: 'contradiction', 1: 'entailment', 2: 'neutral'}.
    """
    res = batch_evaluate_nli([(anchor_text, candidate_text)])
    return res[0]


def batch_evaluate_nli(pairs: List[Tuple[str, str]], batch_size: int = 32) -> List[Dict[str, float]]:
    """
    Evaluates multiple (anchor, candidate) pairs with true batch inference:
    1. Checks in-memory cache for each pair.
    2. Batches all uncached pairs into a SINGLE model.predict call.
    3. Populates cache and returns results in identical query order.
    """
    global EVALUATED_PAIRS_COUNT
    if not pairs:
        return []

    results = [None] * len(pairs)
    uncached_pairs = []
    uncached_indices = []

    clean_pairs = []
    for idx, (a, c) in enumerate(pairs):
        a_trunc = a[:600].strip()
        c_trunc = c[:600].strip()
        pair_key = (a_trunc, c_trunc)
        clean_pairs.append(pair_key)

        if pair_key in _PAIR_CACHE:
            c_p, e_p, n_p = _PAIR_CACHE[pair_key]
            results[idx] = {"contradiction": c_p, "entailment": e_p, "neutral": n_p}
        else:
            uncached_pairs.append((a_trunc, c_trunc))
            uncached_indices.append(idx)

    if uncached_pairs:
        model = get_nli_model()
        logits = model.predict(uncached_pairs, batch_size=batch_size)
        probs = torch.softmax(torch.tensor(logits), dim=-1).tolist()
        EVALUATED_PAIRS_COUNT += len(uncached_pairs)

        for (a_trunc, c_trunc), orig_idx, (c_p, e_p, n_p) in zip(uncached_pairs, uncached_indices, probs):
            _PAIR_CACHE[(a_trunc, c_trunc)] = (float(c_p), float(e_p), float(n_p))
            results[orig_idx] = {
                "contradiction": float(c_p),
                "entailment": float(e_p),
                "neutral": float(n_p)
            }

    return results


def reset_evaluated_pairs_count():
    global EVALUATED_PAIRS_COUNT
    EVALUATED_PAIRS_COUNT = 0


def get_evaluated_pairs_count() -> int:
    return EVALUATED_PAIRS_COUNT
