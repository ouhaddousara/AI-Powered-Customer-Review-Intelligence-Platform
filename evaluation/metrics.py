"""
Layer 8 — Final evaluation of the RAG pipeline.

Loads TEST_SET from evaluation/dataset/rag_evaluation.json (30
hand-annotated questions across 8 categories) rather than a hardcoded
list — see evaluation/annotate.py for how relevant_reviews were
verified against real retrieval output.

Metrics:
1. Precision@k / MRR — retrieval quality (see docstrings below).
2. Faithfulness — LLM-as-judge: does the answer stick to the context?
3. Answer relevance — LLM-as-judge: does the answer actually address
   the question (distinct from faithfulness — an answer can be 100%
   grounded in the context and still miss the point of the question).
4. No-answer accuracy — for questions marked expects_answer=False,
   does the system correctly refuse rather than hallucinate?
5. End-to-end latency.
"""

import json
import time
from collections import defaultdict
from pathlib import Path

from groq import Groq

from src.rag.qa import (
    LLM_MODEL,
    NO_RESULTS_MESSAGE,
    answer_question,
    build_context,
    retrieve_reviews,
)

DATASET_PATH = Path("evaluation/dataset/rag_evaluation.json")

FAITHFULNESS_JUDGE_PROMPT = """You are a strict fact-checker. You will be given \
a CONTEXT (customer reviews) and an ANSWER generated from that context. \

Your job: determine if EVERY factual claim in the ANSWER is directly \
supported by the CONTEXT. 

Respond with exactly one line in this format:
VERDICT: PASS or FAIL
REASON: <one sentence>

FAIL if the answer states anything not present in the context, even a \
small embellishment. PASS only if every claim traces back to the context."""

RELEVANCE_JUDGE_PROMPT = """You are a strict evaluator. You will be given a \
QUESTION and an ANSWER. Your job: determine if the ANSWER actually addresses \
what the QUESTION asked — not whether it's factually correct, just whether \
it's on-topic and responsive.

Respond with exactly one line in this format:
VERDICT: PASS or FAIL
REASON: <one sentence>

FAIL if the answer dodges, misunderstands, or ignores the question's intent."""


def load_dataset() -> list[dict]:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def precision_at_k(question: str, relevant_ids: list[str], top_k: int = 5) -> float:
    results = retrieve_reviews(question, top_k=top_k)
    retrieved_ids = [meta["product_id"] for meta in results["metadatas"][0]]
    if not retrieved_ids:
        return 0.0
    hits = sum(1 for pid in retrieved_ids if pid in relevant_ids)
    return hits / len(retrieved_ids)


def mrr(question: str, relevant_ids: list[str], top_k: int = 5) -> float:
    results = retrieve_reviews(question, top_k=top_k)
    retrieved_ids = [meta["product_id"] for meta in results["metadatas"][0]]
    for rank, pid in enumerate(retrieved_ids, start=1):
        if pid in relevant_ids:
            return 1.0 / rank
    return 0.0


def _judge(prompt_body: str, system_prompt: str, groq_api_key: str) -> bool:
    client = Groq(api_key=groq_api_key)
    completion = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_body},
        ],
        temperature=0.0,
        reasoning_effort="none",
    )
    return "VERDICT: PASS" in completion.choices[0].message.content


def judge_faithfulness(context: str, answer: str, groq_api_key: str) -> bool:
    return _judge(f"CONTEXT:\n{context}\n\nANSWER:\n{answer}", FAITHFULNESS_JUDGE_PROMPT, groq_api_key)


def judge_answer_relevance(question: str, answer: str, groq_api_key: str) -> bool:
    return _judge(f"QUESTION:\n{question}\n\nANSWER:\n{answer}", RELEVANCE_JUDGE_PROMPT, groq_api_key)


def run_evaluation(groq_api_key: str) -> None:
    dataset = load_dataset()
    unannotated = [c for c in dataset if c["relevant_reviews"] is None]
    if unannotated:
        print(
            f"WARNING: {len(unannotated)} questions not yet annotated — "
            f"run `python evaluation/annotate.py` first. Skipping them."
        )
        dataset = [c for c in dataset if c["relevant_reviews"] is not None]

    by_category = defaultdict(list)

    for case in dataset:
        question = case["question"]
        expects_answer = case["expects_answer"]
        print(f"\n=== [{case['category']}] {question} ===")

        start = time.time()
        result = answer_question(question, groq_api_key)
        elapsed = time.time() - start

        if not expects_answer:
            no_answer_correct = result["answer"] == NO_RESULTS_MESSAGE
            print(f"  No-answer check: {'PASS' if no_answer_correct else 'FAIL'}")
            by_category[case["category"]].append({"no_answer_correct": no_answer_correct, "latency": elapsed})
            continue

        p = precision_at_k(question, case["relevant_reviews"])
        m = mrr(question, case["relevant_reviews"])
        print(f"  Precision@5: {p:.2f}  MRR: {m:.2f}  Latency: {elapsed:.2f}s")

        results = retrieve_reviews(question)
        context = build_context(results)
        faithful = judge_faithfulness(context, result["answer"], groq_api_key)
        relevant = judge_answer_relevance(question, result["answer"], groq_api_key)
        print(f"  Faithfulness: {'PASS' if faithful else 'FAIL'}  Answer relevance: {'PASS' if relevant else 'FAIL'}")

        by_category[case["category"]].append({
            "precision": p, "mrr": m, "latency": elapsed,
            "faithful": faithful, "relevant": relevant,
        })

    print("\n\n=== Summary by category ===")
    for category, entries in by_category.items():
        print(f"\n{category} ({len(entries)} questions)")

        scored = [e for e in entries if "precision" in e]
        no_answer_entries = [e for e in entries if "no_answer_correct" in e]

        if scored:
            avg_p = sum(e["precision"] for e in scored) / len(scored)
            avg_m = sum(e["mrr"] for e in scored) / len(scored)
            faith_rate = sum(e["faithful"] for e in scored) / len(scored)
            rel_rate = sum(e["relevant"] for e in scored) / len(scored)
            print(f"  Avg Precision@5: {avg_p:.2f}  Avg MRR: {avg_m:.2f}")
            print(f"  Faithfulness: {faith_rate:.0%}  Answer relevance: {rel_rate:.0%}")

        if no_answer_entries:
            accuracy = sum(e["no_answer_correct"] for e in no_answer_entries) / len(no_answer_entries)
            print(f"  No-answer accuracy: {accuracy:.2f} ({len(no_answer_entries)} questions)")


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()
    run_evaluation(os.getenv("GROQ_API_KEY"))