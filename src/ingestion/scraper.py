"""
Web scraping ingestion.

Collects reviews directly from e-commerce product pages using Scrapy,
and converts scraped items into `Review` objects (see schema.py).

Why this is more involved than csv_loader/json_loader: scraping is the
only ingestion path that can fail mid-run (network errors, site layout
changes, rate limiting) and the only one that raises legal/ethical
considerations (robots.txt, rate limits). Both need to be designed for
up front, not patched in after the first failure.

Decisions to make before writing this for real:
1. Which specific site(s) am I scraping? robots.txt and page structure
   are site-specific — this file can't be finished generically.
2. What's the polite crawl rate (Scrapy's DOWNLOAD_DELAY /
   AUTOTHROTTLE settings)? Set this deliberately, don't leave defaults.
3. What happens on a failed page fetch — retry N times then skip and
   log, not crash the whole run.
"""

from typing import Iterator

import scrapy

from .schema import Review


class ReviewSpider(scrapy.Spider):
    """
    Scrapy spider that crawls product review pages.

    TODO(Layer 1 implementation):
    - name: give this spider a name (Scrapy requires it).
    - start_urls / start_requests: define the product pages to crawl.
    - parse(): extract each review's raw fields (text, rating, date,
      reviewer) from the page HTML using CSS/XPath selectors, and
      yield a plain dict per review (NOT a Review object yet — do the
      conversion to Review in `scraped_items_to_reviews` below, so the
      spider itself stays a thin extraction layer and is easy to swap
      per target site).
    - Respect robots.txt: set ROBOTSTXT_OBEY = True in settings unless
      there's a specific, deliberate reason not to.
    """

    name = "review_spider"

    def parse(self, response):
        raise NotImplementedError


def scraped_items_to_reviews(items: list[dict]) -> Iterator[Review]:
    """
    Convert raw scraped item dicts (as yielded by ReviewSpider.parse)
    into normalized Review objects.

    Keeping this conversion separate from the spider means the spider
    can be rewritten per target site without touching the rest of the
    ingestion pipeline — only the dict shape it produces needs to stay
    consistent.

    TODO(Layer 1 implementation): implement once ReviewSpider.parse
    produces real scraped dicts to test against.
    """
    raise NotImplementedError
