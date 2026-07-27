from pathlib import Path
from src.ingestion import load_json, load_csv
from src.ingestion import load_pdf

pdf_reviews = list(load_pdf(Path("data/raw/sample_review_report.pdf")))
print(f"[PDF] Loaded {len(pdf_reviews)} reviews")
for r in pdf_reviews[:3]:
    print(r)

json_reviews = list(load_json(Path("data/raw/amazon_reviews_sample.jsonl")))
print(f"[JSON] Loaded {len(json_reviews)} reviews")
print(json_reviews[0])

csv_reviews = list(load_csv(Path("data/raw/sample_csv_export.csv")))
print(f"[CSV] Loaded {len(csv_reviews)} reviews")
for r in csv_reviews:
    print(r)

pdf_reviews = list(load_pdf(Path("data/raw/sample_review_report.pdf")))
print(f"[PDF] Loaded {len(pdf_reviews)} reviews")
for r in pdf_reviews[:3]:
    print(r)