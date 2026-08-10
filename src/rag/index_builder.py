"""
Layer 5 — RAG: build the vector index from Review objects.

Chunking strategy: 1 review = 1 chunk — preserves
full review context, and keeps the citation traceable to exactly one
source review, no ambiguity about which part of a merged chunk was
used.
"""


import chromadb
from chromadb.utils import embedding_functions

from src.ingestion.schema import Review

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
PERSIST_DIR = "data/processed/chroma_db"
COLLECTION_NAME = "reviews"


def get_embedding_function():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )


def build_index(reviews: list[Review], persist_dir: str = PERSIST_DIR) -> None:
    """
    Embed each review (1 review = 1 chunk) and store it in a
    persistent ChromaDB collection. Metadata includes per-aspect
    sentiment (from Layer 4, if already computed on the review) so
    queries can filter by sentiment, not just rely on raw semantic
    similarity — a plain similarity search can't tell "positive
    review mentioning X" apart from "negative review mentioning X".
    """
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )

    documents, metadatas, ids = [], [], []
    for review in reviews:
        text = review.text_clean or review.text_raw
        if not text:
            continue

        aspects = review.metadata.get("aspects", {})
        metadata = {
            "product_id": review.product_id,
            "source": review.source,
            "rating": review.rating if review.rating is not None else -1,
            "text_raw": review.text_raw,
        }
        # ChromaDB metadata values must be str/int/float/bool — no None,
        # so a missing aspect becomes the string "none", not null.
        for aspect_name in ("product", "shipping", "service", "price"):
            metadata[f"aspect_{aspect_name}"] = aspects.get(aspect_name) or "none"

        documents.append(text)
        metadatas.append(metadata)
        ids.append(review.review_id)

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"Indexed {len(ids)} reviews into ChromaDB ({persist_dir})")
