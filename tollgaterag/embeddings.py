"""
Offline TF-IDF embedding backend (no model downloads required).

The rest of the pipeline is embedding-agnostic: swap this for
sentence-transformers or an API embedding model without touching scoring/gating.
"""

import os
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from chromadb.api.types import EmbeddingFunction

from tollgaterag import config

VECTORIZER_PATH = os.path.join(config.CHROMA_DIR, "tfidf_vectorizer.pkl")


class TfidfEmbeddingFunction(EmbeddingFunction):
    def __init__(self, vectorizer: TfidfVectorizer = None):
        self.vectorizer = vectorizer

    def __call__(self, input):  # noqa: A002 - Chroma's parameter name
        if self.vectorizer is None:
            raise RuntimeError("No fitted vectorizer. Run `python -m tollgaterag.ingest` first.")
        return self.vectorizer.transform(input).toarray().tolist()

    @staticmethod
    def name() -> str:
        return "tollgaterag_tfidf"

    def get_config(self):
        return {}

    @staticmethod
    def build_from_config(config_dict):
        return TfidfEmbeddingFunction.load()

    @staticmethod
    def fit_and_save(corpus: list) -> "TfidfEmbeddingFunction":
        vectorizer = TfidfVectorizer(max_features=2048, stop_words="english")
        vectorizer.fit(corpus)
        os.makedirs(config.CHROMA_DIR, exist_ok=True)
        with open(VECTORIZER_PATH, "wb") as f:
            pickle.dump(vectorizer, f)
        return TfidfEmbeddingFunction(vectorizer)

    @staticmethod
    def load() -> "TfidfEmbeddingFunction":
        if not os.path.exists(VECTORIZER_PATH):
            raise RuntimeError("No fitted vectorizer. Run `python -m tollgaterag.ingest` first.")
        with open(VECTORIZER_PATH, "rb") as f:
            return TfidfEmbeddingFunction(pickle.load(f))
