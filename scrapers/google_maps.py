"""Scrap Google Maps reviews"""

import logging
import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode
)
from maps_jscodes import (
    JS_ACCEPT_COOKIES,
    JS_SCROLL_LOAD
)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("GMaps Reviews Scraper")


async def scrap_google_maps_reviews(url: str, show_console_messages: bool = False):
    """
    Scrap Google Maps reviews for a given URL.
    """

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
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

        scroll_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id="maps",
            js_code=JS_SCROLL_LOAD,
            wait_for='js:() => document.body.getAttribute("data-crawl-ready") === "1"',
            wait_for_timeout=300000,
            delay_before_return_html=5,
            js_only=True,
            capture_console_messages=True,
        )
        result = await crawler.arun(url=url, config=scroll_config)

        if show_console_messages:
            for msg in result.console_messages:
                print(msg)

    logger.info("Scraping finished.")

    return result


if __name__ == "__main__":
    url_google_reviews = "https://www.google.com/maps/place/Apotheke+Berlin+Hauptbahnhof/@52.5254862,13.3673304,16z/data=!3m1!5s0x12009d62009e027f:0xfe6df7e9b440aa0b!4m8!3m7!1s0x479ebd4cdc0644e1:0xbb66f36efe28ecd4!8m2!3d52.525483!4d13.3699107!9m1!1b1!16s%2Fg%2F1hc5v5zhc?entry=ttu&g_ep=EgoyMDI2MDUxNy4wIKXMDSoASAFQAw%3D%3D"
    reviews = asyncio.run(
        scrap_google_maps_reviews(url=url_google_reviews,
        show_console_messages=True)
    )
    print(reviews)
