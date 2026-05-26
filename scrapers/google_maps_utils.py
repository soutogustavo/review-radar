"""Utils for google maps scraper"""

import re
import logging
from bs4 import BeautifulSoup
from prefect import task

logging.root.setLevel(logging.INFO)
logger = logging.getLogger("Google Maps Utils")


@task
def parse_maps_reviews_from_html(html: str) -> list[dict]:
    """
    Parse reviews from HTML.

    Args:
    - html (str): HTML content to parse.

    Returns:
    - list[dict]: List of reviews.
    """

    logger.info("Parsing reviews...")
    soup = BeautifulSoup(html, "html.parser")
    reviews = soup.find_all("div", class_="jftiEf")

    results = []
    for review in reviews:
        rating_el = review.find("span", class_="kvMYJc")
        rating = 0
        if rating_el:
            match = re.search(r"(\d+)", rating_el.get("aria-label", ""))
            rating = int(match.group(1)) if match else 0

        text_el = review.find("span", class_="wiI7pd")

        date_el = review.find("span", class_="rsqaWe")

        likes_el = review.find("span", class_="pkWtMe")

        author_el = review.find("div", class_="d4r55")
        author = author_el.get_text(strip=True) if author_el else ""

        results.append({
            "review": text_el.get_text(strip=True) if text_el else "",
            "rating": rating,
            "date":   date_el.get_text(strip=True) if date_el else "",
            "likes":  int(likes_el.get_text(strip=True)) if likes_el else 0,
            "_author_hash_only": author,
        })

    return results
