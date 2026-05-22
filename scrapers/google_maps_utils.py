"""Utils for scraper"""

import re
import logging
from bs4 import BeautifulSoup

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("Utils")


def parse_reviews_from_html(html: str) -> list[dict]:
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

        results.append({
            "review": text_el.get_text(strip=True) if text_el else "",
            "rating": rating,
            "date":   date_el.get_text(strip=True) if date_el else "",
            "likes":  int(likes_el.get_text(strip=True)) if likes_el else 0,
        })

    logger.info("Parsed %s reviews", len(results))
    return results
