"""
Layer 4 — NLP Analysis: entity extraction (brands, SKUs).

Brands: extracted via a pretrained NER model (ORG entities) — avoids
needing to hand-maintain a brand list, which wouldn't scale across
product categories.

SKUs: extracted via regex, not NER — a SKU has a recognizable format
(uppercase letters + digits), a pattern match is more reliable here
than a general-purpose entity model.
"""

import re

from transformers import pipeline

from src.ingestion.schema import Review

SKU_PATTERN = re.compile(r"\b[A-Z]{1,3}\d{4,}[A-Z0-9]*\b")

_ner_pipeline = None


def _get_ner_pipeline():
    global _ner_pipeline
    if _ner_pipeline is None:
        _ner_pipeline = pipeline(
            "ner",
            model="dslim/bert-base-NER",
            aggregation_strategy="simple",
        )
    return _ner_pipeline


def extract_brands(text: str) -> list[str]:
    """
    Includes both ORG and MISC entity groups
    """
    ner = _get_ner_pipeline()
    entities = ner(text[:512])
    brands = {
        e["word"].strip()
        for e in entities
        if e["entity_group"] in ("ORG", "MISC")
    }
    return sorted(brands)


def extract_skus(text: str) -> list[str]:
    return sorted(set(SKU_PATTERN.findall(text)))


def extract_entities(review: Review) -> Review:
    """
    Populate review.metadata["entities"] with detected brands and SKUs,
    using text_clean (falls back to text_raw). Mutates and returns the
    same Review object.
    """
    text = review.text_clean or review.text_raw
    review.metadata["entities"] = {
        "brands": extract_brands(text),
        "skus": extract_skus(text),
    }
    return review
