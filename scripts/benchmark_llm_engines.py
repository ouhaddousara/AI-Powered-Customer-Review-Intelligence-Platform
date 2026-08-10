"""
Benchmark Groq/LLaMA 3, Qwen (via Groq), and Mistral on the same
review-context questions, using the retrieval already validated in
qa.py — isolates the comparison to LLM generation quality, not
retrieval.

Note: Gemini was originally planned (per the project proposal) but
excluded here — the free-tier API key returned 429 RESOURCE_EXHAUSTED
on every request (quota locked at 0, a known issue on unbilled Gemini
API accounts as of late 2025/2026). Qwen was substituted instead,
served directly through Groq's free tier (no new account/billing
needed) — a real competing model, not an arbitrary stand-in.

llama-3.3-70b-versatile was announced deprecated by Groq (2026-06-17)
but still functional as of this benchmark — worth migrating to
qwen/qwen3.6-27b or openai/gpt-oss-120b later.

Usage:
    python scripts/benchmark_llm_engines.py
"""

import os
import time

from dotenv import load_dotenv
from groq import Groq
from mistralai.client import Mistral

from src.rag.qa import retrieve_reviews, build_context, SYSTEM_PROMPT

load_dotenv()

TEST_QUESTIONS = [
    "What do customers complain about most?",
    "What do customers love about these products?",
    "Are there any mentions of product size or fit issues?",
    "What do people say about shipping and delivery?",
    "Which products get the most praise for value for money?",
]


def run_groq(context: str, question: str) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        temperature=0.2,
    )
    return completion.choices[0].message.content


def run_qwen(context: str, question: str) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    completion = client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        temperature=0.2,
        reasoning_effort="none",
    )
    return completion.choices[0].message.content


def run_mistral(context: str, question: str) -> str:
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
    completion = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        temperature=0.2,
    )
    return completion.choices[0].message.content


def main() -> None:
    engines = {"groq_llama3": run_groq, "qwen": run_qwen, "mistral": run_mistral}
    results = {name: {"total_time": 0.0, "answers": []} for name in engines}

    for question in TEST_QUESTIONS:
        print(f"\n=== {question} ===")
        retrieval = retrieve_reviews(question)
        context = build_context(retrieval)

        for engine_name, run_fn in engines.items():
            start = time.time()
            try:
                answer = run_fn(context, question)
            except Exception as e:
                answer = f"[ERROR: {e}]"
            elapsed = time.time() - start

            results[engine_name]["total_time"] += elapsed
            results[engine_name]["answers"].append(answer)
            print(f"\n--- {engine_name} ({elapsed:.2f}s) ---")
            print(answer[:300])

    print("\n\n=== Summary ===")
    for engine_name, data in results.items():
        avg_time = data["total_time"] / len(TEST_QUESTIONS)
        print(f"{engine_name:15s} avg_time={avg_time:.2f}s  total_time={data['total_time']:.1f}s")


if __name__ == "__main__":
    main()