"""
Layer 5 — RAG: build the vector index from Review objects.

Chunking strategy: 1 review = 1 chunk — preserves
full review context, and keeps the citation traceable to exactly one
source review, no ambiguity about which part of a merged chunk was
used.
"""

from pathlib import Path
from typing import List

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


def build_index(reviews: List[Review], persist_dir: str = PERSIST_DIR) -> None:
    """
    Embed each review (1 review = 1 chunk) and store it in a
    persistent ChromaDB collection, along with metadata needed for
    citation (product_id, rating, source).
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

        documents.append(text)
        metadatas.append({
            "product_id": review.product_id,
            "source": review.source,
            "rating": review.rating if review.rating is not None else -1,
            "text_raw": review.text_raw,
        })
        ids.append(review.review_id)

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"Indexed {len(ids)} reviews into ChromaDB ({persist_dir})")
