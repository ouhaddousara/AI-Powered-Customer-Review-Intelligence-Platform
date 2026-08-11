"""
Unit tests for RAG retrieval behavior (src/rag/qa.py).

Deliberately test only ChromaDB-level logic (no LLM calls) — keeps
these tests runnable in CI without needing GROQ_API_KEY as a secret.
"""

from src.rag.qa import check_relevance, detect_sentiment_filter, is_relevant


def test_detect_sentiment_filter_negative_intent():
    assert detect_sentiment_filter("What do customers complain about?") == "negative"


def test_detect_sentiment_filter_positive_intent():
    assert detect_sentiment_filter("What do customers love?") == "positive"


def test_detect_sentiment_filter_no_intent():
    assert detect_sentiment_filter("What products are mentioned?") is None


def test_relevant_question_passes_check():
    assert check_relevance("What do customers complain about most?") is True


def test_off_topic_question_fails_check():
    assert check_relevance("What is the capital of France?") is False


def test_relevance_check_unaffected_by_sentiment_filter():
    """
    Regression test for the coupling bug fixed earlier: relevance for
    a sentiment-triggering question ("complain") must be evaluated on
    the same basis as any other question — it should pass if the
    topic genuinely exists in the corpus, independent of the filter
    later applied during retrieval.
    """
    assert check_relevance("What do customers complain about most?") is True


def test_is_relevant_handles_empty_distances():
    empty_results = {"distances": [[]]}
    assert is_relevant(empty_results) is False
