"""
Layer 4 — NLP Analysis: aspect-based sentiment.

Approach: fixed aspect list (product/shipping/service/price), detected
per sentence via keyword matching (FR/EN, since ground-truth data mixes
both), then a multilingual sentiment model scores each sentence that
mentions an aspect. Results are aggregated per aspect per review.

Why keyword-based aspect detection instead of a trained classifier:
with only 4 fixed aspects and clear vocabulary, keyword matching is
simpler, fully interpretable, and avoids needing labeled training data
we don't have — a reasonable first version, not a permanent ceiling.
"""

import re
from collections import defaultdict
from typing import Optional

from transformers import pipeline

from src.ingestion.schema import Review

ASPECT_KEYWORDS = {
    "product": [
        "product", "quality", "produit", "qualité", "material", "matière",
    ],
    "shipping": [
        "shipping", "delivery", "livraison", "shipped", "arrived", "package",
        "colis", "livré",
    ],
    "service": [
        "service", "support", "customer service", "seller", "vendeur",
        "service client",
    ],
    "price": [
        "price", "prix", "expensive", "cher", "cheap", "value", "worth",
        "coûte",
    ],
}

_sentiment_pipeline = None


def _get_sentiment_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
        )
    return _sentiment_pipeline


def split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s for s in sentences if s]


def detect_aspects(sentence: str) -> list[str]:
    sentence_lower = sentence.lower()
    return [
        aspect
        for aspect, keywords in ASPECT_KEYWORDS.items()
        if any(kw in sentence_lower for kw in keywords)
    ]


def _stars_to_label(star_label: str) -> str:
    # nlptown model outputs "1 star" .. "5 stars"
    stars = int(star_label[0])
    if stars <= 2:
        return "negative"
    if stars == 3:
        return "neutral"
    return "positive"


def analyze_aspects(text: str) -> dict[str, Optional[str]]:
    sentiment = _get_sentiment_pipeline()
    aspect_sentences = defaultdict(list)

    for sentence in split_sentences(text):
        for aspect in detect_aspects(sentence):
            aspect_sentences[aspect].append(sentence)

    # Fallback: a review that mentions none of shipping/service/price is
    # implicitly about the product — classifying it as "no aspect found"
    # would be misleading, since the review clearly has *a* subject.
    if not aspect_sentences:
        aspect_sentences["product"].append(text)

    results: dict[str, Optional[str]] = {aspect: None for aspect in ASPECT_KEYWORDS}
    for aspect, sentences in aspect_sentences.items():
        combined = " ".join(sentences)[:512]
        prediction = sentiment(combined)[0]
        results[aspect] = _stars_to_label(prediction["label"])

    return results


def analyze_review(review: Review) -> Review:
    """
    Populate review.metadata["aspects"] with per-aspect sentiment,
    using text_clean (falls back to text_raw if preprocessing wasn't
    run). Mutates and returns the same Review object.
    """
    text = review.text_clean or review.text_raw
    review.metadata["aspects"] = analyze_aspects(text)
    return review
