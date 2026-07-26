"""
One-shot script to re-export a subset of the already-downloaded Amazon
Reviews sample as a CSV file, simulating a retailer CSV export. Reuses
real review data — only the file format changes.

One row is intentionally blanked out (empty review_text) to validate
that csv_loader.py correctly skips incomplete rows — this is the only
synthetic modification; everything else is real review content.

Usage:
    python scripts/export_csv_sample.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

INPUT_PATH = Path("data/raw/amazon_reviews_sample.jsonl")
OUTPUT_PATH = Path("data/raw/sample_csv_export.csv")
SAMPLE_SIZE = 200


def main() -> None:
    rows = []
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= SAMPLE_SIZE:
                break
            raw = json.loads(line)
            review_date = datetime.fromtimestamp(
                raw["timestamp"] / 1000, tz=timezone.utc
            ).date().isoformat()

            rows.append({
                "review_id": f"{raw['user_id']}{raw['timestamp']}",
                "product_id": raw.get("parent_asin") or raw.get("asin"),
                "review_text": raw.get("text"),
                "star_rating": raw.get("rating"),
                "review_date": review_date,
            })

    # Intentionally blank one row's text, to test csv_loader's skip logic
    rows[3]["review_text"] = ""

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"Saved {len(rows)} rows to {OUTPUT_PATH} (1 row intentionally blanked for testing)")


if __name__ == "__main__":
    main()
