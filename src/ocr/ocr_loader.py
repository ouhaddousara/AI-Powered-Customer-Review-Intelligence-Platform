"""
Layer 3 — OCR ingestion.

Extracts text from review images using Tesseract, chosen after a
3-engine benchmark (see scripts/benchmark_ocr_engines.py):
Tesseract avg_score=0.126 (best, normalized Levenshtein), 3.9s total.
EasyOCR: 0.193, 14.9s. PaddleOCR: excluded — environment
incompatibility (paddlepaddle 3.3.x oneDNN/CPU bug) and, once
worked around, produced unusable output (score 1.116, 95.2s).
"""

from collections.abc import Iterator
from pathlib import Path

import pytesseract
from PIL import Image

from src.ingestion.schema import Review, make_review_id

SOURCE_NAME = "ocr"


def load_images(directory: Path) -> Iterator[Review]:
    """
    Run Tesseract OCR on every image in a directory and yield a
    Review per image. product_id is unknown at this stage (real
    review screenshots carry no product metadata) — set to the
    image filename stem as a placeholder, to be resolved later if a
    mapping becomes available.
    """
    skipped = 0
    image_paths = sorted(directory.glob("*.jpg")) + sorted(directory.glob("*.png"))

    for image_path in image_paths:
        text = pytesseract.image_to_string(Image.open(image_path)).strip()

        if not text:
            skipped += 1
            continue

        product_id = image_path.stem
        yield Review(
            review_id=make_review_id(SOURCE_NAME, image_path.name),
            product_id=product_id,
            source=SOURCE_NAME,
            text_raw=text,
        )

    if skipped:
        print(f"[ocr_loader] Skipped {skipped} images with no extractable text in {directory}")
       
