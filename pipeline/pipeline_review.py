"""Review Radar Pipeline"""
import logging
import asyncio
from prefect import flow

from scrapers.google_maps import scrap_google_maps_reviews
from scrapers.google_maps_utils import parse_reviews_from_html

from pipeline.db import load_active_sources
from pipeline.models import ClientSource

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("Review Pipeline")


@flow(name="Review Pipeline")
def review_pipeline(client: ClientSource, headless: bool = True, show_console_messages: bool = False):

    if client.platform == "google_maps":
        scraped_reviews = asyncio.run(
            scrap_google_maps_reviews(
                url=client.url,
                headless=headless,
                show_console_messages=show_console_messages
        )
    )
        reviews = parse_reviews_from_html(html=scraped_reviews.html)

    return reviews


if __name__ == "__main__":

    clients = load_active_sources()

    for client in clients:
        print(f"Scraping reviews for client {client.client_name}")

        reviews = review_pipeline(
            client=client,
            headless=False,
            show_console_messages=False
        )

        print(f"Scraped {len(reviews)} reviews")
