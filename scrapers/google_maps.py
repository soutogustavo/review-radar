"""Scrap Google Maps reviews"""

import logging
import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode
)
from prefect import task
from scrapers.google_maps_jscodes import (
    JS_ACCEPT_COOKIES,
    JS_SCROLL_LOAD
)
from scrapers.google_maps_utils import parse_maps_reviews_from_html

logging.root.setLevel(logging.INFO)
logger = logging.getLogger("Google Maps Scraper")


@task
async def scrap_google_maps_reviews(
    url: str, show_console_messages: bool = False,
    headless: bool = True
) -> str:
    """
    Scrap Google Maps reviews for a given URL.

    Args:
        url (str): URL of the Google Maps page.
        show_console_messages (bool): Whether to show console messages.
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        str: HTML content of the page.

    """

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=headless,
        verbose=False,
        java_script_enabled=True,
    )

    logger.info("Start scraping...")
    async with AsyncWebCrawler(config=browser_config) as crawler:
        accept_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id="maps",
            js_code=JS_ACCEPT_COOKIES,
            delay_before_return_html=5,
        )
        await crawler.arun(url=url, config=accept_config)


        logger.info("Scrolling to load all reviews...")
        stable_rounds = 0
        last_loaded = -1
        max_stable_rounds = 4

        while True:
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    session_id="maps",
                    js_code=JS_SCROLL_LOAD,
                    wait_for='js:() => document.body.getAttribute("data-crawl-ready") === "1"',
                    delay_before_return_html=2,
                    js_only=True,
                    capture_console_messages=True,
                )
            )

            html = result.html or ""
            loaded_now = html.count('data-review-id')
            if loaded_now == 0:
                loaded_now = html.count('jftiEf')

            if loaded_now <= last_loaded:
                stable_rounds += 1
            else:
                stable_rounds = 0

            last_loaded = loaded_now

            if stable_rounds >= max_stable_rounds:
                break

        if show_console_messages:

            if result.success and result.console_messages:
                for msg in result.console_messages:
                    if msg.get("type") == "error":
                        logger.info(f"Console Error: {msg.get('text')}")

    logger.info("Scraping finished.")

    return result


if __name__ == "__main__":
    url_google_reviews = "https://www.google.com/maps/..." # Reviews section
    result = asyncio.run(
        scrap_google_maps_reviews(url=url_google_reviews,
        show_console_messages=True)
    )

    reviews = parse_maps_reviews_from_html(result.html)
    logger.info(f"Scraped {len(reviews)} reviews")
