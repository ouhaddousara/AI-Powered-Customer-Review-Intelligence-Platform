from pathlib import Path

from src.ingestion import load_csv, load_json, load_pdf
from src.preprocessing import preprocess_review

sources = {
    "json": list(load_json(Path("data/raw/amazon_reviews_sample.jsonl")))[:5],
    "csv": list(load_csv(Path("data/raw/sample_csv_export.csv")))[:5],
    "pdf": list(load_pdf(Path("data/raw/sample_review_report.pdf")))[:5],
}

for source_name, reviews in sources.items():
    print(f"\n--- {source_name} ---")
    for r in reviews:
        preprocess_review(r)
        print(f"lang={r.language} | raw={r.text_raw[:60]!r} | clean={r.text_clean[:60]!r}")
