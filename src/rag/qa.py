"""
Layer 5 — RAG: question answering with source citation.

Critical design decision: the LLM is instructed to answer ONLY from
the retrieved reviews, never from its own general knowledge, and to
say so explicitly when the context doesn't contain the answer — this
is what makes the system's answers verifiable rather than plausible
guesses.

Sentiment-aware retrieval: plain similarity search finds text on the
right topic but can't distinguish a positive review from a negative
one mentioning the same subject — it ranks by semantic closeness, not
sentiment polarity. detect_sentiment_filter() catches simple intent
signals in the question ("complaints", "love") and filters the search
to reviews where Layer 4's aspect sentiment matches, using metadata
already stored at indexing time.

Model choice: Qwen 3.6 27B (via Groq), switched from LLaMA 3.3 70B
after benchmarking (see docs/llm_benchmark.md) — better handling of
multilingual nuance, and LLaMA 3.3 70B is deprecated by Groq (2026-06-17).
reasoning_effort="none" is REQUIRED — Qwen is a reasoning model that
otherwise leaks its internal <think> trace into the response.
"""

from typing import List, Optional

from groq import Groq
import chromadb

from src.rag.index_builder import get_embedding_function, PERSIST_DIR, COLLECTION_NAME

LLM_MODEL = "qwen/qwen3.6-27b"
TOP_K = 5

NEGATIVE_INTENT_KEYWORDS = [
    "complain", "problem", "issue", "wrong", "worst", "disappoint",
    "défaut", "problème", "plainte", "pire",
]
POSITIVE_INTENT_KEYWORDS = [
    "love", "best", "great", "recommend",
    "aime", "meilleur", "recommand",
]

SYSTEM_PROMPT = """You are a product review analyst. Answer the user's \
question using ONLY the customer reviews provided in the context below. \

Rules:
- Do not use any knowledge beyond what is in the provided reviews.
- If the reviews don't contain enough information to answer, say so \
explicitly — do not guess or infer beyond what is stated.
- When you make a claim, mention which review supports it (by product ID).
- Be concise and factual, not promotional."""


def get_collection():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    return client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )


def detect_sentiment_filter(question: str) -> Optional[str]:
    """
    Simple keyword-based intent detection — same approach as the
    aspect keyword matching in Layer 4, for consistency. Returns
    "negative", "positive", or None (no filter, rely on similarity
    alone).
    """
    q = question.lower()
    if any(kw in q for kw in NEGATIVE_INTENT_KEYWORDS):
        return "negative"
    if any(kw in q for kw in POSITIVE_INTENT_KEYWORDS):
        return "positive"
    return None


def retrieve_reviews(question: str, top_k: int = TOP_K) -> dict:
    collection = get_collection()
    sentiment_filter = detect_sentiment_filter(question)

    where_clause = None
    if sentiment_filter:
        where_clause = {
            "$or": [
                {f"aspect_{aspect}": sentiment_filter}
                for aspect in ("product", "shipping", "service", "price")
            ]
        }

    return collection.query(
        query_texts=[question],
        n_results=top_k,
        where=where_clause,
    )


def build_context(results: dict) -> str:
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    context_parts = []
    for doc, meta in zip(documents, metadatas):
        context_parts.append(
            f"[Product {meta['product_id']}, rating {meta['rating']}/5] {doc}"
        )
    return "\n\n".join(context_parts)


def answer_question(question: str, groq_api_key: str, top_k: int = TOP_K) -> dict:
    """
    Returns {"answer": str, "sources": list of {product_id, rating, text_raw}}.
    """
    results = retrieve_reviews(question, top_k)
    context = build_context(results)

    client = Groq(api_key=groq_api_key)
    completion = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        temperature=0.2,
        reasoning_effort="none",
    )

    sources = [
        {
            "product_id": meta["product_id"],
            "rating": meta["rating"],
            "text_raw": meta["text_raw"],
        }
        for meta in results["metadatas"][0]
    ]

    return {
        "answer": completion.choices[0].message.content,
        "sources": sources,
    }