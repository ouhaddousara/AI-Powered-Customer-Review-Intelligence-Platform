"""
Layer 1 — Data Ingestion.

Public entry point for this layer. Downstream code (preprocessing,
notebooks) should import from here, not reach into individual loader
modules directly — this keeps the internal split between
csv_loader/json_loader/scraper as an implementation detail that can
change without breaking callers.
"""

from .schema import Review, make_review_id
from .csv_loader import load_csv
from .json_loader import load_json
from .scraper import ReviewSpider, scraped_items_to_reviews

__all__ = [
    "Review",
    "make_review_id",
    "load_csv",
    "load_json",
    "ReviewSpider",
    "scraped_items_to_reviews",
]
