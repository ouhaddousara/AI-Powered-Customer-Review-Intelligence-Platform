"""
CSV ingestion.

Loads reviews from a CSV export (e.g. a retailer's review export) and
converts each row into a `Review` (see schema.py).

Why this is its own module and not inlined elsewhere: CSV exports vary
a lot in column naming between retailers. Isolating that mapping logic
here means adapting to a new CSV format only touches this file.
"""

from pathlib import Path
from typing import Iterator

from .schema import Review


# Expected column mapping. Adjust this once you have a real CSV sample —
# this is the first thing to check when a new CSV source doesn't parse.
COLUMN_MAPPING = {
    "review_id": "review_id",
    "product_id": "product_id",
    "text": "review_text",
    "rating": "star_rating",
    "date": "review_date",
}


def load_csv(path: Path) -> Iterator[Review]:
    """
    Read a CSV file and yield one Review per valid row.

    Implementation notes for when you write this:
    - Use pandas.read_csv (already a project dependency) rather than the
      stdlib csv module — it handles encoding/quoting edge cases better
      and integrates naturally with the rest of the pandas-based pipeline.
    - Rows missing a required field (text, product_id) should be skipped
      and counted, not silently dropped — log or return a count so the
      caller knows how much data was rejected.
    - Do not assume the CSV is UTF-8. Reviews often contain non-ASCII
      characters (accents, emojis) — handle encoding errors explicitly
      rather than letting pandas guess.

    Args:
        path: path to the CSV file.

    Yields:
        Review objects, one per valid row.

    TODO(Layer 1 implementation): implement using pandas + COLUMN_MAPPING.
    """
    raise NotImplementedError
