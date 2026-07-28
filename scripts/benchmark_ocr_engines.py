"""
Benchmark Tesseract, EasyOCR, and PaddleOCR against the ground-truth
text of the degraded review images, scoring each with normalized
Levenshtein distance (0 = perfect match, higher = worse).

Usage:
    python scripts/benchmark_ocr_engines.py
"""

import json
import time
from pathlib import Path

import pytesseract
import easyocr
from paddleocr import PaddleOCR
from PIL import Image
import Levenshtein

IMAGES_DIR = Path("data/raw/ocr_test_images")
GROUND_TRUTH_PATH = IMAGES_DIR / "ground_truth.json"


def score(predicted: str, truth: str) -> float:
    """
    Normalized Levenshtein distance: edit distance divided by the
    length of the reference text, so scores are comparable across
    reviews of different lengths. 0 = perfect, 1 = completely wrong.
    """
    if not truth:
        return 1.0
    return Levenshtein.distance(predicted, truth) / len(truth)


def run_tesseract(image_path: Path) -> str:
    return pytesseract.image_to_string(Image.open(image_path)).strip()


def run_easyocr(reader, image_path: Path) -> str:
    results = reader.readtext(str(image_path), detail=0)
    return " ".join(results).strip()


def run_paddleocr(engine, image_path: Path) -> str:
    result = engine.ocr(str(image_path))
    if not result or not result[0]:
        return ""
    return " ".join(line[1][0] for line in result[0]).strip()


def main() -> None:
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    easyocr_reader = easyocr.Reader(["en"], gpu=False)
    paddle_engine = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang="en",
)

    engines = {
        "tesseract": lambda p: run_tesseract(p),
        "easyocr": lambda p: run_easyocr(easyocr_reader, p),
        "paddleocr": lambda p: run_paddleocr(paddle_engine, p),
    }

    results = {name: {"scores": [], "total_time": 0.0} for name in engines}

    for filename, truth in ground_truth.items():
        image_path = IMAGES_DIR / filename
        print(f"\n{filename}")

        for engine_name, run_fn in engines.items():
            start = time.time()
            predicted = run_fn(image_path)
            elapsed = time.time() - start

            s = score(predicted, truth)
            results[engine_name]["scores"].append(s)
            results[engine_name]["total_time"] += elapsed

            print(f"  {engine_name:12s} score={s:.3f}  ({elapsed:.2f}s)")

    print("\n=== Summary ===")
    for engine_name, data in results.items():
        avg_score = sum(data["scores"]) / len(data["scores"])
        print(
            f"{engine_name:12s} avg_score={avg_score:.3f}  "
            f"total_time={data['total_time']:.1f}s"
        )


if __name__ == "__main__":
    main()
