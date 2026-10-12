"""
Loads .txt documents (SOURCE / TRUST_LEVEL / DATE / TITLE header + body),
embeds them, and builds the local Chroma collection.

In production, SOURCE and TRUST_LEVEL would come from your document management
or identity system, not from a text header.
"""

import os
import re
import glob
import chromadb

from tollgaterag import config
from tollgaterag.embeddings import TfidfEmbeddingFunction

HEADER_PATTERN = re.compile(
    r"SOURCE:\s*(?P<source>.*)\r?\n"
    r"TRUST_LEVEL:\s*(?P<trust_level>.*)\r?\n"
    r"DATE:\s*(?P<date>.*)\r?\n"
    r"TITLE:\s*(?P<title>.*)\r?\n\r?\n"
    r"(?P<body>.*)",
    re.DOTALL,
)


def parse_document(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    match = HEADER_PATTERN.match(raw)
    if not match:
        return {"id": os.path.basename(path), "source": "unknown", "trust_level": "unknown",
                "date": "1970-01-01", "title": os.path.basename(path), "body": raw.strip()}
    doc = match.groupdict()
    doc["id"] = os.path.basename(path)
    doc["trust_level"] = doc["trust_level"].strip().lower()
    for k in ("source", "date", "title", "body"):
        doc[k] = doc[k].strip()
    return doc


def load_documents(data_dir: str = config.DATA_DIR) -> list:
    return [parse_document(p) for p in sorted(glob.glob(os.path.join(data_dir, "*.txt")))]


def build_index(reset: bool = True):
    os.makedirs(config.CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=config.CHROMA_DIR)
    if reset:
        try:
            client.delete_collection(config.COLLECTION_NAME)
        except Exception:
            pass

    docs = load_documents()
    if not docs:
        raise RuntimeError(f"No documents found in {config.DATA_DIR}")

    embed_fn = TfidfEmbeddingFunction.fit_and_save([d["body"] for d in docs])
    collection = client.get_or_create_collection(name=config.COLLECTION_NAME, embedding_function=embed_fn)
    collection.add(
        ids=[d["id"] for d in docs],
        documents=[d["body"] for d in docs],
        metadatas=[{"source": d["source"], "trust_level": d["trust_level"],
                    "date": d["date"], "title": d["title"]} for d in docs],
    )
    print(f"Indexed {len(docs)} documents into Chroma collection '{config.COLLECTION_NAME}'.")
    return collection


if __name__ == "__main__":
    build_index(reset=True)
