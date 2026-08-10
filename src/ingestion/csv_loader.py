"""
CSV ingestion — retailer CSV export format.
"""

from collections.abc import Iterator
from pathlib import Path

import pandas as pd

from .schema import Review, make_review_id

SOURCE_NAME = "csv"

COLUMN_MAPPING = {
    "review_id": "review_id",
    "product_id": "product_id",
    "text": "review_text",
    "rating": "star_rating",
    "date": "review_date",
}


def load_csv(path: Path) -> Iterator[Review]:
    df = pd.read_csv(path, encoding="utf-8", dtype=str)

    skipped = 0
    for _, row in df.iterrows():
        text = row.get(COLUMN_MAPPING["text"])
        product_id = row.get(COLUMN_MAPPING["product_id"])

        if pd.isna(text) or pd.isna(product_id):
            skipped += 1
            continue

        original_id = row.get(COLUMN_MAPPING["review_id"])
        if pd.isna(original_id):
            skipped += 1
            continue

        review_id = make_review_id(SOURCE_NAME, str(original_id))

        rating_raw = row.get(COLUMN_MAPPING["rating"])
        rating = int(float(rating_raw)) if not pd.isna(rating_raw) else None

        date_raw = row.get(COLUMN_MAPPING["date"])
        review_date = None
        if not pd.isna(date_raw):
            parsed = pd.to_datetime(date_raw, errors="coerce")
            if not pd.isna(parsed):
                review_date = parsed.date()

        yield Review(
            review_id=review_id,
            product_id=str(product_id),
            source=SOURCE_NAME,
            text_raw=str(text),
            rating=rating,
            review_date=review_date,
        )

    if skipped:
        print(f"[csv_loader] Skipped {skipped} malformed/incomplete rows in {path}")