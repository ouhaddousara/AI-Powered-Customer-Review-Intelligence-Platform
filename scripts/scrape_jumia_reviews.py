"""
Combine product discovery (Scrapy output) with review extraction
(Selenium) into a single Jumia reviews dataset.

Usage:
    1. First generate the product list:
       scrapy runspider src/ingestion/jumia_scraper.py \
           -o data/raw/jumia_products.jsonl -s CLOSESPIDER_ITEMCOUNT=50

    2. Then run this script:
       python scripts/scrape_jumia_reviews.py
"""

import json
import re
import time
from pathlib import Path

from src.ingestion.jumia_scraper import (
    fetch_reviews_page_html,
    make_driver,
    parse_reviews,
)

PRODUCTS_PATH = Path("data/raw/jumia_products.jsonl")
OUTPUT_PATH = Path("data/raw/jumia_reviews.jsonl")

# Politeness delay between products, on top of the Cloudflare wait
# already inside fetch_reviews_page_html — stays well under Jumia's
# stated 200 req/min limit.
DELAY_BETWEEN_PRODUCTS_SECONDS = 3


def extract_reviews_link_and_id(driver, product_url: str):
    """
    Visit a product page, find its reviews page link and product ID
    from the URL (the numeric suffix before .html).
    """
    driver.get(product_url)
    time.sleep(8)  # same Cloudflare wait as the reviews page

    match = re.search(r"-(\d+)\.html", product_url)
    product_id = match.group(1) if match else product_url

    from parsel import Selector
    sel = Selector(text=driver.page_source)
    reviews_link = sel.css('a[href*="productratingsreviews"]::attr(href)').get()

    return reviews_link, product_id


def main() -> None:
    products = []
    with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            products.append(json.loads(line)["product_url"])

    print(f"Loaded {len(products)} product URLs")

    driver = make_driver()
    total_reviews = 0
    skipped = 0

    try:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as out_file:
            for i, product_url in enumerate(products, start=1):
                print(f"[{i}/{len(products)}] {product_url}")

                reviews_link, product_id = extract_reviews_link_and_id(driver, product_url)
                if not reviews_link:
                    print("  -> no reviews link found, skipping")
                    skipped += 1
                    continue

                full_reviews_url = (
                    reviews_link if reviews_link.startswith("http")
                    else f"https://www.jumia.ma{reviews_link}"
                )
                html = fetch_reviews_page_html(full_reviews_url, driver)
                reviews = list(parse_reviews(html, product_id))

                out_file.writelines(json.dumps(review.to_dict(), ensure_ascii=False) + "\n" for review in reviews)

                print(f"  -> {len(reviews)} reviews")
                total_reviews += len(reviews)

                time.sleep(DELAY_BETWEEN_PRODUCTS_SECONDS)
    finally:
        driver.quit()

    print(f"\nDone. {total_reviews} reviews from {len(products) - skipped} products "
          f"({skipped} skipped, no reviews link).")


if __name__ == "__main__":
    main()
