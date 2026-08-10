from pathlib import Path

from src.ingestion import load_csv, load_json, load_pdf
from src.ocr import load_images

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

ocr_reviews = list(load_images(Path("data/raw/ocr_test_images")))
print(f"[OCR] Loaded {len(ocr_reviews)} reviews")
for r in ocr_reviews[:3]:
    print(r)