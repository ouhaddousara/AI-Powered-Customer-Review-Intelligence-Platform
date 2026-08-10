"""
JSON Lines ingestion — Amazon Reviews 2023 format (McAuley Lab).
"""

import json
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

from .schema import Review, make_review_id

SOURCE_NAME = "json"


def load_json(path: Path) -> Iterator[Review]:
    skipped = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue

            text = raw.get("text")
            product_id = raw.get("parent_asin") or raw.get("asin")
            if not text or not product_id:
                skipped += 1
                continue

            original_id = raw.get("user_id", "") + str(raw.get("timestamp", ""))
            review_id = make_review_id(SOURCE_NAME, original_id)

            timestamp_ms = raw.get("timestamp")
            review_date = None
            if timestamp_ms:
                review_date = datetime.fromtimestamp(
                    timestamp_ms / 1000, tz=timezone.utc
                ).date()

            yield Review(
                review_id=review_id,
                product_id=product_id,
                source=SOURCE_NAME,
                text_raw=text,
                rating=raw.get("rating"),
                review_date=review_date,
                metadata={
                    "title": raw.get("title"),
                    "verified_purchase": raw.get("verified_purchase"),
                    "helpful_vote": raw.get("helpful_vote"),
                },
            )

    if skipped:
        print(f"[json_loader] Skipped {skipped} malformed/incomplete lines in {path}")