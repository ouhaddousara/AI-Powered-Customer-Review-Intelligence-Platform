"""
Common review schema — shared data contract for all ingestion sources.
"""

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional


@dataclass
class Review:
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
        d = asdict(self)
        if self.review_date is not None:
            d["review_date"] = self.review_date.isoformat()
        return d


def make_review_id(source: str, original_id: str) -> str:
    raw = f"{source}:{original_id}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()