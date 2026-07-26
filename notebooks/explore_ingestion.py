from pathlib import Path
from src.ingestion import load_json

reviews = list(load_json(Path("data/raw/amazon_reviews_sample.jsonl")))

print(f"Loaded {len(reviews)} reviews")
print(reviews[0])
print(reviews[0].to_dict())
