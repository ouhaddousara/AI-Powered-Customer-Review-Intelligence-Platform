"""
Layer 8 — Final evaluation of the RAG pipeline.

Three metrics, each measuring something distinct from the benchmarks
done earlier (which compared tools; this measures the system built
with the chosen tools):

1. Precision@k — NOT recall (true recall would require knowing every
   relevant review in the 5000+ corpus, infeasible to hand-annotate).
   Measures, of the k retrieved reviews, how many are genuinely
   relevant, checked against a small hand-verified test set.
2. Faithfulness — LLM-as-judge: a second model call checks whether
   every claim in the answer is actually supported by the retrieved
   context, catching hallucination that a human skim might miss.
3. End-to-end latency — question in, answer out, real wall-clock time.
"""

import time
from dataclasses import dataclass, field
from typing import List

from groq import Groq

from src.rag.qa import answer_question, retrieve_reviews, LLM_MODEL

JUDGE_SYSTEM_PROMPT = """You are a strict fact-checker. You will be given \
a CONTEXT (customer reviews) and an ANSWER generated from that context. \

Your job: determine if EVERY factual claim in the ANSWER is directly \
supported by the CONTEXT. 

Respond with exactly one line in this format:
VERDICT: PASS or FAIL
REASON: <one sentence>

FAIL if the answer states anything not present in the context, even a \
small embellishment. PASS only if every claim traces back to the context."""


@dataclass
class TestCase:
    question: str
    # Product IDs manually verified as genuinely relevant to the question —
    # a hand-checked subset, not an exhaustive corpus-wide ground truth.
    relevant_product_ids: List[str] = field(default_factory=list)


# Hand-verified against real retrieval output seen during development —
# each product_id below was manually confirmed relevant to its question.
TEST_SET = [
    TestCase(
        question="What do customers complain about most?",
        relevant_product_ids=["B0749FJSN2", "B0929H24R1", "B073WQHFXB", "B0008F6QGO"],
    ),
    TestCase(
        question="Are there any mentions of product size or fit issues?",
        relevant_product_ids=["B08BBQ29N5", "B07TK6647L"],
    ),
    TestCase(
        question="What do people say about shipping and delivery?",
        relevant_product_ids=["B0855LGCNX", "B01LW6VB7M", "B077R9DW9L", "B082D4T8PM", "B07DWMKCFD"],
    ),
    TestCase(
        question="Which products get the most praise for value for money?",
        relevant_product_ids=["B08RNQNFW1", "B0133YZ22U"],
    ),
    TestCase(
        question="What do customers love about these products?",
        relevant_product_ids=["B08393CSHT", "B008S59834", "B01BZVADRW"],
    ),
]


def precision_at_k(question: str, relevant_ids: List[str], top_k: int = 5) -> float:
    results = retrieve_reviews(question, top_k=top_k)
    retrieved_ids = [meta["product_id"] for meta in results["metadatas"][0]]
    if not retrieved_ids:
        return 0.0
    hits = sum(1 for pid in retrieved_ids if pid in relevant_ids)
    return hits / len(retrieved_ids)


def judge_faithfulness(context: str, answer: str, groq_api_key: str) -> dict:
    """
    Uses the same model family (Qwen via Groq) as a judge, in a
    separate call with no access to the original question — only
    context + answer — so it evaluates grounding, not plausibility.
    """
    client = Groq(api_key=groq_api_key)
    completion = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": f"CONTEXT:\n{context}\n\nANSWER:\n{answer}"},
        ],
        temperature=0.0,
        reasoning_effort="none",
    )
    verdict_text = completion.choices[0].message.content.strip()
    passed = "VERDICT: PASS" in verdict_text
    return {"passed": passed, "raw": verdict_text}


def run_evaluation(groq_api_key: str) -> None:
    from src.rag.qa import build_context

    precisions, latencies, faithfulness_results = [], [], []

    for case in TEST_SET:
        print(f"\n=== {case.question} ===")

        # Precision@k
        p = precision_at_k(case.question, case.relevant_product_ids)
        precisions.append(p)
        print(f"  Precision@5: {p:.2f}")

        # Latency + faithfulness (needs the actual answer + context)
        start = time.time()
        results = retrieve_reviews(case.question)
        context = build_context(results)
        result = answer_question(case.question, groq_api_key)
        elapsed = time.time() - start
        latencies.append(elapsed)
        print(f"  Latency: {elapsed:.2f}s")

        judgment = judge_faithfulness(context, result["answer"], groq_api_key)
        faithfulness_results.append(judgment["passed"])
        print(f"  Faithfulness: {'PASS' if judgment['passed'] else 'FAIL'} — {judgment['raw']}")

    print("\n=== Summary ===")
    print(f"Avg Precision@5: {sum(precisions) / len(precisions):.2f}")
    print(f"Avg Latency: {sum(latencies) / len(latencies):.2f}s")
    print(f"Faithfulness pass rate: {sum(faithfulness_results)}/{len(faithfulness_results)}")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    run_evaluation(os.getenv("GROQ_API_KEY"))
