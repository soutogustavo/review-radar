"""Review Radar Pipeline"""

import logging
import asyncio
from datetime import datetime
from prefect import flow

from scrapers.google_maps import scrap_google_maps_reviews
from scrapers.google_maps_utils import parse_maps_reviews_from_html

from pipeline.db import load_active_sources
from pipeline.models import ClientSource
from pipeline.tasks import save_run

logging.root.setLevel(logging.INFO)
logger = logging.getLogger("Pipeline")


@flow(name="Review Pipeline")
def review_pipeline(
    client: ClientSource
):
    """Review pipeline

    Args:
        client (ClientSource): Client source data

    Returns:
        list[dict]: List of reviews
    """

    started_at = datetime.utcnow()

    if client.platform == "google_maps":
        scraped_reviews = asyncio.run(
            scrap_google_maps_reviews(
                url=client.url,
                headless=client.scrape_config.headless,
                show_console_messages=client.scrape_config.show_console_messages
            )
        )
        reviews = parse_maps_reviews_from_html(html=scraped_reviews.html)

    save_run(
        run=client,
        reviews=reviews,
        anomaly={},
        started_at=started_at
    )

    return reviews


if __name__ == "__main__":

    clients = load_active_sources()

    for client in clients:
        logger.info(f"Scraping reviews for client {client.client_name}")

        reviews = review_pipeline(
            client=client
        )

        logger.info(f"Scraped {len(reviews)} reviews")
        logger.info(reviews)
