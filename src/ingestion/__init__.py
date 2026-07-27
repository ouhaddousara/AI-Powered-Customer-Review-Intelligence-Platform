"""
Layer 1 — Data Ingestion.

Public entry point for this layer. Downstream code (preprocessing,
notebooks) should import from here, not reach into individual loader
modules directly.
"""

from .schema import Review, make_review_id
from .csv_loader import load_csv
from .json_loader import load_json
from .pdf_loader import load_pdf

__all__ = [
    "Review",
    "make_review_id",
    "load_csv",
    "load_json",
    "load_pdf"
]
