"""
One-shot script to generate OCR test images from real review text.

Renders real Amazon reviews as text images, then applies realistic
degradation (blur, noise, slight rotation, JPEG compression) so the
OCR benchmark actually differentiates engines — perfectly clean
renders would score ~100% on all three and prove nothing.

Also saves a ground_truth.json mapping each image to its exact
source text, needed to score OCR output objectively (Levenshtein
distance) in the next step.

Usage:
    python scripts/generate_ocr_test_images.py
"""

import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

import textwrap

INPUT_PATH = Path("data/raw/amazon_reviews_sample.jsonl")
OUTPUT_DIR = Path("data/raw/ocr_test_images")
SAMPLE_SIZE = 15

random.seed(42)


def render_text_image(text: str) -> Image.Image:
    wrapped_lines = textwrap.wrap(text[:250], width=65)
    line_height = 18
    img_height = max(200, line_height * len(wrapped_lines) + 20)

    img = Image.new("RGB", (500, img_height), color="white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.multiline_text((10, 10), "\n".join(wrapped_lines), fill="black", font=font)
    return img


def degrade_image(img: Image.Image) -> Image.Image:
    img = img.rotate(random.uniform(-2, 2), fillcolor="white")
    img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.8)))

    arr = np.array(img).astype(np.int16)
    noise = np.random.normal(0, 8, arr.shape).astype(np.int16)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ground_truth = {}

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= SAMPLE_SIZE:
                break
            raw = json.loads(line)
            text = (raw.get("text") or "").strip()
            if not text:
                continue

            img = render_text_image(text)
            img = degrade_image(img)

            filename = f"review_{i:02d}.jpg"
            img.save(OUTPUT_DIR / filename, quality=70)  # lossy, adds compression artifacts
            ground_truth[filename] = text[:250]

    with open(OUTPUT_DIR / "ground_truth.json", "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(ground_truth)} degraded review images in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
