"""
Jumia.ma review scraping.

Two parts in this file:
1. JumiaProductDiscoverySpider (Scrapy) — crawls category pages to find
   product URLs. Works with Scrapy's normal downloader because category
   and product pages are NOT behind Cloudflare's challenge.
2. make_driver / fetch_reviews_page_html / parse_reviews (Selenium) —
   fetches and parses a single product's reviews page. Uses Selenium
   because THIS specific page IS behind Cloudflare's JS challenge,
   which blocks Scrapy's default downloader (same issue as curl).

Known limitation: the reviews page only ever exposes the 10 most
recent reviews per product — no working pagination was found (URL
param and scroll-triggered API calls were both tested and ruled out).
Coverage is achieved by scraping more products, not more reviews per
product.
"""

import re
import time
from collections.abc import Iterator
from datetime import datetime

from parsel import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from src.ingestion.schema import Review, make_review_id

SOURCE_NAME = "jumia_scraping"
CLOUDFLARE_WAIT_SECONDS = 8


# --- Product discovery (finds product URLs from category pages) ---


class JumiaProductDiscoverySpider(CrawlSpider):
    name = "jumia_product_discovery"
    allowed_domains = ["jumia.ma"]

    start_urls = [
        "https://www.jumia.ma/smartphones/",
    ]

    rules = (
        Rule(
            LinkExtractor(allow=r"\?page=\d+", restrict_css=".pg-w a"),
            follow=True,
        ),
        Rule(
            LinkExtractor(allow=r"-\d+\.html"),
            callback="parse_product",
        ),
    )

    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "AUTOTHROTTLE_ENABLED": True,
        "ROBOTSTXT_OBEY": True,
    }

    def parse_product(self, response):
        yield {"product_url": response.url}


# --- Review extraction (Selenium, needed to pass Cloudflare) ---


def make_driver() -> webdriver.Chrome:
    """
    Build a headless Chrome driver configured to look like a real
    browser — needed to pass Jumia's Cloudflare JS challenge.
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
    return webdriver.Chrome(options=options)


def fetch_reviews_page_html(url: str, driver: webdriver.Chrome) -> str:
    """
    Load a Jumia product reviews page and return its fully-rendered
    HTML, waiting long enough for Cloudflare's challenge to resolve.
    """
    driver.get(url)
    time.sleep(CLOUDFLARE_WAIT_SECONDS)
    return driver.page_source


def parse_reviews(html: str, product_id: str) -> Iterator[Review]:
    """
    Parse the reviews page HTML into Review objects.

    Each review is an <article> inside the "div.cola" container:
        <article class="-pvm -hr _bet">
          <div class="stars _m _al -mvm">5 out of 5<div class="in" .../></div>
          <h3 class="-m -fs16 -pvm">Title</h3>
          <p class="-pvm">Body</p>
          <div class="-df -j-bet -i-ctr -gy5">
            <div class="-pvm"><span class="-prm">DD-MM-YYYY</span><span>par Author</span></div>
            <div>...Achat vérifié</div>
          </div>
        </article>
    """
    sel = Selector(text=html)
    review_blocks = sel.css("div.cola article")

    for block in review_blocks:
        rating = _parse_rating(block.css("div.stars::text").get(""))

        title = (block.css("h3::text").get("") or "").strip()
        body = (block.css("p::text").get("") or "").strip()
        text = f"{title}. {body}".strip(". ").strip()
        if not text:
            continue

        spans = block.css("div.-pvm span::text").getall()
        date_text = spans[0] if len(spans) > 0 else ""
        author = spans[1].replace("par ", "").strip() if len(spans) > 1 else ""
        review_date = _parse_date(date_text)
        verified = "Achat vérifié" in block.get()

        original_id = f"{product_id}:{date_text}:{author}:{title}"
        yield Review(
            review_id=make_review_id(SOURCE_NAME, original_id),
            product_id=product_id,
            source=SOURCE_NAME,
            text_raw=text,
            rating=rating,
            review_date=review_date,
            metadata={"author": author, "verified_purchase": verified},
        )


def _parse_rating(text: str) -> int | None:
    match = re.match(r"(\d)", text.strip())
    return int(match.group(1)) if match else None


def _parse_date(text: str):
    match = re.search(r"(\d{2}-\d{2}-\d{4})", text)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%d-%m-%Y").date()
    except ValueError:
        return None