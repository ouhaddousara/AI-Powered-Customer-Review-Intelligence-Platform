"""
Layer 1 — Data Ingestion.

Public entry point for this layer. Downstream code (preprocessing,
notebooks) should import from here, not reach into individual loader
modules directly.
"""

from .csv_loader import load_csv
from .json_loader import load_json
from .pdf_loader import load_pdf
from .schema import Review, make_review_id

__all__ = [
    "Review",
    "load_csv",
    "load_json",
    "load_pdf",
    "make_review_id"
]
