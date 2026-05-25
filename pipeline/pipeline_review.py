"""Review Radar Pipeline"""
import logging
import asyncio
from prefect import flow

from scrapers.google_maps import scrap_google_maps_reviews
from scrapers.google_maps_utils import parse_reviews_from_html

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("Review Pipeline")


@flow(name="Review Pipeline")
def review_pipeline(url: str, headless: bool = True, show_console_messages: bool = False):

    scraped_reviews = asyncio.run(
        scrap_google_maps_reviews(
            url=url,
            headless=headless,
            show_console_messages=show_console_messages
        )
    )

    reviews = parse_reviews_from_html(html=scraped_reviews.html)

    return reviews


if __name__ == "__main__":
    url_google_reviews = "https://www.google.com/maps/..." # Reviews section

    reviews = review_pipeline(
        url=url_google_reviews,
        headless=False,
        show_console_messages=False
    )

    print(f"Scraped {len(reviews)} reviews")
