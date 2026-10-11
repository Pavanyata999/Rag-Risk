"""Retrieval layer: top-k candidates plus the set of verified 'anchor' documents."""

import chromadb

from tollgaterag import config
from tollgaterag.embeddings import TfidfEmbeddingFunction


class Retriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=config.CHROMA_DIR)
        self.embed_fn = TfidfEmbeddingFunction.load()
        self.collection = self.client.get_or_create_collection(
            name=config.COLLECTION_NAME, embedding_function=self.embed_fn
        )
        self._anchors = None

    def retrieve(self, query: str, top_k: int = None) -> list:
        top_k = top_k or config.TOP_K_RETRIEVE
        n = min(top_k, self.collection.count())
        res = self.collection.query(query_texts=[query], n_results=n,
                                    include=["documents", "metadatas", "distances"])
        out = []
        for rank, (doc_id, body, meta, dist) in enumerate(
            zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0])
        ):
            out.append({
                "id": doc_id, "title": meta.get("title", doc_id),
                "source": meta.get("source", "unknown"),
                "trust_level": meta.get("trust_level", "unknown"),
                "date": meta.get("date", "1970-01-01"),
                "body": body, "distance": dist, "rank": rank,
            })
        return out

    def verified_anchors(self) -> list:
        """All verified documents in the corpus (not just the retrieved ones)."""
        if self._anchors is None:
            res = self.collection.get(where={"trust_level": "verified"},
                                      include=["documents", "metadatas"])
            self._anchors = [
                {"id": i, "title": m.get("title", i), "body": b}
                for i, b, m in zip(res["ids"], res["documents"], res["metadatas"])
            ]
        return self._anchors
