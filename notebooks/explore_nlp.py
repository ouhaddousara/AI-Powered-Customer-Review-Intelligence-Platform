from src.ingestion import load_json
from src.preprocessing import preprocess_review
from src.nlp import analyze_review
from pathlib import Path
from src.nlp import extract_entities

all_reviews = list(load_json(Path("data/raw/amazon_reviews_sample.jsonl")))

reviews = all_reviews[:20]
detected_count = 0
for r in reviews:
    preprocess_review(r)
    analyze_review(r)
    aspects_found = {k: v for k, v in r.metadata["aspects"].items() if v is not None}
    if aspects_found:
        detected_count += 1
        print(r.text_raw[:80])
        print(aspects_found)
        print()



test_reviews = [r for r in all_reviews if any(
    brand in r.text_raw for brand in ["Amazon", "Sonicare", "Phillips", "NYX", "Tresemme", "Sally Hansen"]
)]
print(f"\nFound {len(test_reviews)} reviews mentioning known brands")

for r in test_reviews[:5]:
    extract_entities(r)
    print(r.text_raw[:100])
    print(r.metadata["entities"])
    print()


print(f"\n{detected_count}/20 reviews had at least one aspect detected")
