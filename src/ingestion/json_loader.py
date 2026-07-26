"""
JSON ingestion.

Loads reviews from a JSON feed (list of review objects, or a JSON Lines
file) and converts each entry into a `Review` (see schema.py).

Why this is separate from csv_loader.py even though both are "flat file"
sources: JSON feeds are often nested (e.g. reviews grouped under a
product object) while CSVs are always flat rows. Keeping them separate
avoids a loader that tries to handle both shapes and ends up fragile.
"""

from pathlib import Path
from typing import Iterator

from .schema import Review


def load_json(path: Path) -> Iterator[Review]:
    """
    Read a JSON file and yield one Review per entry.

    Implementation notes for when you write this:
    - Support two shapes at minimum: a flat list of review objects, and
      a JSON Lines file (one JSON object per line) — the latter is
      common for large exports since it can be streamed instead of
      loaded fully into memory.
    - Detect which shape it is (e.g. by trying to parse the first line
      as standalone JSON) rather than requiring the caller to specify it.
    - Same rule as csv_loader: skip and count invalid entries rather than
      crashing on the first malformed record — a 50,000-review export
      having 12 bad entries shouldn't block ingestion of the other
      49,988.

    Args:
        path: path to the JSON or JSON Lines file.

    Yields:
        Review objects, one per valid entry.

    TODO(Layer 1 implementation): implement, detecting list-JSON vs
    JSON-Lines format.
    """
    raise NotImplementedError
