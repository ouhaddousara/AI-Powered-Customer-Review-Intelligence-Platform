"""
Unit tests for RAG retrieval behavior (src/rag/qa.py).

Deliberately test only ChromaDB-level logic (no LLM calls) — keeps
most of these tests runnable in CI without needing GROQ_API_KEY as a
secret.

Three tests (marked @requires_real_index) need the actual indexed
corpus to exist on disk. data/processed/ (where ChromaDB persists) is
git-ignored by design, same as data/raw/ — CI has no built index and
correctly skips these rather than failing. Run them locally after
building the index via src.rag.index_builder.build_index().
"""

from pathlib import Path

import pytest

from src.rag import qa

INDEX_EXISTS = Path(qa.PERSIST_DIR).exists()

requires_real_index = pytest.mark.skipif(
    not INDEX_EXISTS,
    reason=(
        "Requires the real indexed corpus (data/processed/chroma_db), "
        "which is git-ignored and not built in CI."
    ),
)


def test_detect_sentiment_filter_negative_intent():
    assert qa.detect_sentiment_filter("What do customers complain about?") == "negative"


def test_detect_sentiment_filter_positive_intent():
    assert qa.detect_sentiment_filter("What do customers love?") == "positive"


def test_detect_sentiment_filter_no_intent():
    assert qa.detect_sentiment_filter("What products are mentioned?") is None


@requires_real_index
def test_relevant_question_passes_check():
    assert qa.check_relevance("What do customers complain about most?") is True


@requires_real_index
def test_off_topic_question_fails_check():
    assert qa.check_relevance("What is the capital of France?") is False


@requires_real_index
def test_relevance_check_unaffected_by_sentiment_filter():
    """
    Regression test for the coupling bug fixed earlier: relevance for
    a sentiment-triggering question ("complain") must be evaluated on
    the same basis as any other question — it should pass if the
    topic genuinely exists in the corpus, independent of the filter
    later applied during retrieval.
    """
    assert qa.check_relevance("What do customers complain about most?") is True


def test_is_relevant_handles_empty_distances():
    empty_results = {"distances": [[]]}
    assert qa.is_relevant(empty_results) is False
