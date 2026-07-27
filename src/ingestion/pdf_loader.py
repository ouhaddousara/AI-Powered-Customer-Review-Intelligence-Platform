"""
PDF ingestion — retailer-style review report format.

Extracts the review table (Product ID / Rating / Review / Date) from
a PDF report using pdfplumber's table extraction, and converts each
row into a Review (see schema.py).
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Iterator

import pdfplumber

from .schema import Review, make_review_id

SOURCE_NAME = "pdf"


def load_pdf(path: Path) -> Iterator[Review]:
    skipped = 0

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Skip header rows (repeated on each page via repeatRows)
                    if row[0] in (None, "Product ID"):
                        continue

                    product_id, rating_raw, review_text, date_raw = (row + [None] * 4)[:4]

                    if not review_text or not product_id:
                        skipped += 1
                        continue

                    rating = None
                    if rating_raw:
                        match = re.match(r"\d", rating_raw.strip())
                        rating = int(match.group()) if match else None

                    review_date = None
                    if date_raw:
                        try:
                            review_date = datetime.strptime(
                                date_raw.strip(), "%Y-%m-%d"
                            ).date()
                        except ValueError:
                            review_date = None

                    original_id = f"{product_id}:{date_raw}:{review_text[:50]}"
                    yield Review(
                        review_id=make_review_id(SOURCE_NAME, original_id),
                        product_id=product_id.strip(),
                        source=SOURCE_NAME,
                        text_raw=review_text.strip(),
                        rating=rating,
                        review_date=review_date,
                    )

    if skipped:
        print(f"[pdf_loader] Skipped {skipped} malformed/incomplete rows in {path}")
