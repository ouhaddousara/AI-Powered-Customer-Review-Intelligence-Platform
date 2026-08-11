"""
Interactive annotation helper for rag_evaluation.json.

For every question with relevant_reviews == null, runs the real
retrieval against ChromaDB and asks you to confirm which of the
top-5 results are genuinely relevant — turns a blind guessing task
into a quick "yes/no per candidate" review against real data.

Usage:
    python evaluation/annotate.py
"""

import json
from pathlib import Path

from src.rag.qa import retrieve_reviews

DATASET_PATH = Path("evaluation/dataset/rag_evaluation.json")


def main() -> None:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    for case in dataset:
        if case["relevant_reviews"] is not None:
            continue

        print(f"\n{'='*60}\n{case['question']}  [{case['category']}]\n{'='*60}")
        results = retrieve_reviews(case["question"], top_k=5)

        relevant = []
        for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
            print(f"\n[{meta['product_id']}, {meta['rating']}★] {doc[:150]}")
            answer = input("Relevant? (y/n/skip question): ").strip().lower()
            if answer == "skip":
                relevant = None
                break
            if answer == "y":
                relevant.append(meta["product_id"])

        if relevant is not None:
            case["relevant_reviews"] = relevant
            DATASET_PATH.write_text(
                json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(f"Saved: {relevant}")


if __name__ == "__main__":
    main()
