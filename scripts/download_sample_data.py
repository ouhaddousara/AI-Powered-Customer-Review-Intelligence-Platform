"""
One-shot script to download a sample of the Amazon Reviews 2023 dataset
(All_Beauty category) into data/raw/ for local development and testing.

Downloads directly from the raw JSONL file hosted on Hugging Face,
streaming line by line and stopping once SAMPLE_SIZE reviews have been
collected — avoids pulling the entire category file just to keep 5000
lines of it.

Usage:
    python scripts/download_sample_data.py
"""

from pathlib import Path

import requests

DATA_URL = (
    "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023"
    "/resolve/main/raw/review_categories/All_Beauty.jsonl"
)
SAMPLE_SIZE = 5000
OUTPUT_PATH = Path("data/raw/amazon_reviews_sample.jsonl")


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"Streaming from {DATA_URL} ...")
    count = 0
    with requests.get(DATA_URL, stream=True) as response:
        response.raise_for_status()
        with open(OUTPUT_PATH, "w", encoding="utf-8") as out_file:
            for line in response.iter_lines():
                if not line:
                    continue
                out_file.write(line.decode("utf-8") + "\n")
                count += 1
                if count >= SAMPLE_SIZE:
                    break

    print(f"Saved {count} reviews to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()