import os

import chromadb
from dotenv import load_dotenv

from src.rag.index_builder import COLLECTION_NAME, PERSIST_DIR, get_embedding_function
from src.rag.qa import (
    answer_question,
    detect_sentiment_filter,
    get_collection,
)

client = chromadb.PersistentClient(path=PERSIST_DIR)
collection = client.get_collection(
    name=COLLECTION_NAME,
    embedding_function=get_embedding_function(),
)

print(f"Nombre total de reviews indexées : {collection.count()}")

# Aperçu des 5 premiers documents stockés
preview = collection.peek(limit=5)
for doc, meta, id_ in zip(preview["documents"], preview["metadatas"], preview["ids"]):
    print(f"\nID: {id_}")
    print(f"Product: {meta['product_id']} | Rating: {meta['rating']}")
    print(f"Texte: {doc[:100]}...")

# Test de la recherche par similarité
results = collection.query(query_texts=["defective product broke quickly"], n_results=3)
print("\n--- Résultat recherche par similarité ---")
for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    print(f"[{meta['product_id']}] {doc[:100]}...")


load_dotenv()

question = "What do customers complain about most?"
print(f"\nFiltre détecté : {detect_sentiment_filter(question)}")

result = answer_question(question=question, groq_api_key=os.getenv("GROQ_API_KEY"))

print("\n--- Réponse du LLM ---")
print(result["answer"])
print("\n--- Sources citées ---")
for src in result["sources"]:
    print(f"[{src['product_id']}, rating {src['rating']}] {src['text_raw'][:80]}...")


collection = get_collection()

# Question clairement pertinente
relevant = collection.query(query_texts=["What do customers complain about most?"], n_results=5)
print("Pertinente :", relevant["distances"][0])

# Question clairement hors-sujet
irrelevant = collection.query(query_texts=["What is the capital of France?"], n_results=5)
print("Hors-sujet :", irrelevant["distances"][0])


failing_questions = [
    "What's the weather like today?",
    "Who won the last football World Cup?",
    "What is the best programming language?",
    "Can you recommend a good restaurant nearby?",
]

for q in failing_questions:
    results = collection.query(query_texts=[q], n_results=5)  # no filter, matches check_relevance
    distances = results["distances"][0]
    avg = sum(distances) / len(distances)
    print(f"{q}\n  avg_distance={avg:.3f}")