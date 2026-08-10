"""
Common review schema — shared data contract for all ingestion sources.
"""

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import date


@dataclass
class Review:
    review_id: str
    product_id: str
    source: str
    text_raw: str
    text_clean: str | None = None
    rating: int | None = None
    review_date: date | None = None
    language: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.review_date is not None:
            d["review_date"] = self.review_date.isoformat()
        return d


def make_review_id(source: str, original_id: str) -> str:
    raw = f"{source}:{original_id}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()