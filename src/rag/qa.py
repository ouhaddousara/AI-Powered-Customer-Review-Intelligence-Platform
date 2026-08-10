"""
Layer 5 — RAG: question answering with source citation.

Critical design decision: the LLM is instructed to answer ONLY from
the retrieved reviews, never from its own general knowledge, and to
say so explicitly when the context doesn't contain the answer — this
is what makes the system's answers verifiable rather than plausible
guesses.
"""

from typing import List

from groq import Groq

from src.rag.index_builder import get_embedding_function, PERSIST_DIR, COLLECTION_NAME
import chromadb

LLM_MODEL = "llama-3.3-70b-versatile"
TOP_K = 5

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


def retrieve_reviews(question: str, top_k: int = TOP_K) -> dict:
    collection = get_collection()
    return collection.query(query_texts=[question], n_results=top_k)


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
