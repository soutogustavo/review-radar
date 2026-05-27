"""Utils for google maps scraper"""

import re
import hashlib
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

    logger.info(f"Parsed/extracted {len(results)} reviews")

    return results


def normalize_date(date_str: str) -> str:
    """Remove 'Edited' prefix if exists"""
    return re.sub(r"^[Ee]dited\s+", "", date_str).strip()


def generate_review_hash(source_id: str, review: dict) -> str:
    """
    Generate hash for a review.
    Uses source_id + author + normalized_date + rating
    """

    author = review.get("_author_hash_only", "")
    normalized_date = normalize_date(review["date"])
    raw = f"{source_id}|{author}|{normalized_date}|{review['rating']}"

    return hashlib.sha256(raw.encode()).hexdigest()
