"""
Layer 2 — Text preprocessing.

Scope: technical cleaning + light normalization only (HTML artifacts, whitespace noise) — NOT 
bag-of-words style normalization (no lowercasing, no punctuation
stripping, no stopword removal). The pipeline is built around
transformers (sentiment analysis in Layer 4, embeddings in Layer 5),
which need natural text, not aggressively stripped text.

text_raw is never modified — this function only populates text_clean.
"""

import html
import re

from langdetect import LangDetectException, detect

from src.ingestion.schema import Review


def clean_text(text: str) -> str:
    """
    Technical cleaning only:
    - Decode HTML entities (&amp; -> &)
    - Strip HTML tags (<br />, <a href=...>...</a>), keeping their
      text content
    - Collapse internal newlines and repeated whitespace into single
      spaces
    - Trim leading/trailing whitespace

    Deliberately NOT done here : lowercasing,
    punctuation removal, stopword removal — a transformer needs that
    signal intact.
    """
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


MIN_CHARS_FOR_LANG_DETECTION = 20


def detect_language(text: str) -> str | None:
    """
    Detect language on the cleaned text. Returns None (rather than a
    guess) below MIN_CHARS_FOR_LANG_DETECTION — langdetect's
    statistical model is unreliable on short text (a few words isn't
    enough signal to distinguish similar European languages), so a
    wrong guess is worse than admitting we don't know.
    """
    if not text or len(text.strip()) < MIN_CHARS_FOR_LANG_DETECTION:
        return None
    try:
        return detect(text)
    except LangDetectException:
        return None


def preprocess_review(review: Review) -> Review:
    """
    Populate text_clean and language on a Review, leaving text_raw
    untouched. Returns the same Review object, mutated in place.
    """
    cleaned = clean_text(review.text_raw)
    review.text_clean = cleaned
    review.language = detect_language(cleaned)
    return review
