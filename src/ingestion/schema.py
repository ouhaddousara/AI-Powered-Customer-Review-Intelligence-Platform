"""
Common review schema.

Why this file exists:
Every ingestion source (web scraping, CSV, JSON) has a different raw
format. Instead of letting each loader produce its own shape and
reconciling differences downstream, every loader in this package must
convert its raw records into this single `Review` structure before
returning them. This is the "contract" the rest of the pipeline
(preprocessing, NLP, RAG) is built against.

Design decision: keep both the raw text AND a placeholder for cleaned
text. The raw text is needed later for source citation in the RAG
layer (Layer 5) — never overwrite it during preprocessing.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Review:
    """
    A single normalized customer review, regardless of where it came from.

    Attributes:
        review_id: Unique identifier for this review. Must be stable and
            deterministic (e.g. a hash of source + original_id) so the
            same review ingested twice from the same source is detected
            as a duplicate, not as two different reviews.
        product_id: Identifier of the product/SKU this review refers to.
        source: Where this review came from — one of "scraping", "csv",
            "json", "pdf", "ocr". Used later for traceability/citation.
        text_raw: The original, untouched review text. Never modify this
            after ingestion — preprocessing writes to text_clean instead.
        text_clean: Populated by the preprocessing layer (Layer 2). Left
            as None at ingestion time.
        rating: Star rating if available (e.g. 1-5). None if not provided
            by the source.
        review_date: Date the review was posted, if known.
        language: ISO language code if known at ingestion time (rarely
            known this early — usually detected in preprocessing).
        metadata: Anything source-specific worth keeping (e.g. reviewer
            name, verified-purchase flag) that doesn't fit the fields
            above. Keep this small — it's an escape hatch, not a dumping
            ground.
    """

    review_id: str
    product_id: str
    source: str
    text_raw: str
    text_clean: Optional[str] = None
    rating: Optional[int] = None
    review_date: Optional[date] = None
    language: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Convert to a plain dict for JSON serialization.

        TODO(Layer 1 implementation): decide how `review_date` should be
        serialized (isoformat string) and implement it here once the
        loaders are being tested against real data.
        """
        raise NotImplementedError


def make_review_id(source: str, original_id: str) -> str:
    """
    Build a stable, deterministic review_id from a source name and the
    review's original identifier (whatever the source calls it — could
    be a scraped review's DOM position, a CSV row index, or a JSON key).

    Why this matters: this is the function that makes deduplication
    across sources possible. Two loaders producing the same
    (source, original_id) pair must produce the same review_id.

    TODO(Layer 1 implementation): implement using a hash
    (e.g. hashlib.sha1) of f"{source}:{original_id}".
    """
    raise NotImplementedError
