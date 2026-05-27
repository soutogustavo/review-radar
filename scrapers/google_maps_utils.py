"""Utils for google maps scraper"""

import re
import hashlib
import logging
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from prefect import task

logging.root.setLevel(logging.INFO)
logger = logging.getLogger("Google Maps Utils")


@task
def parse_maps_reviews_from_html(html: str, source_id: str) -> list[dict]:
    """
    Parse reviews from HTML.

    Args:
        html (str): HTML content to parse.
        source_id (str): Source ID.

    Returns:
        list[dict]: List of reviews.
    """

    logger.info("Parsing reviews...")
    soup = BeautifulSoup(html, "html.parser")
    reviews = soup.find_all("div", class_="jftiEf")
    scraped_at  = datetime.utcnow()
    results = []

    for review in reviews:
        rating_el = review.find("span", class_="kvMYJc")
        rating = 0
        if rating_el:
            match = re.search(r"(\d+)", rating_el.get("aria-label", ""))
            rating = int(match.group(1)) if match else 0

        text_el = review.find("span", class_="wiI7pd")

        date_el = review.find("span", class_="rsqaWe")
        date_raw = date_el.get_text(strip=True) if date_el else ""

        likes_el = review.find("span", class_="pkWtMe")

        author_el = review.find("div", class_="d4r55")
        author = author_el.get_text(strip=True) if author_el else ""

        row = {
            "review": text_el.get_text(strip=True) if text_el else "",
            "rating": rating,
            "date_raw": date_raw,
            **parse_relative_date(date_raw, scraped_at),
            "likes":  int(likes_el.get_text(strip=True)) if likes_el else 0,
            "_author_hash_only": author,
        }
        row["review_hash"] = generate_review_hash(source_id, row)

        results.append(row)

    logger.info(f"Parsed/extracted {len(results)} reviews")

    return results


def normalize_date(date_str: str) -> str:
    """Remove 'Edited' prefix if exists"""
    return re.sub(r"^[Ee]dited\s+", "", date_str).strip()


def parse_relative_date(date_str: str, scraped_at: datetime = None) -> dict:
    """
    Convert relative date to estimated date.

    Args:
        date_str: Relative date string (ex: "2 years ago", "Edited 3 months ago")
        scraped_at: Scraping time. Default: utcnow()

    Returns:
        dict with estimated_date (YYYY-MM-DD | None) and precision (day/week/month/year/unknown)
    """
    if scraped_at is None:
        scraped_at = datetime.utcnow()

    clean = normalize_date(date_str)

    patterns = [
        (r'(\d+)\s+day[s]?\s+ago',   "day",   lambda n: scraped_at - timedelta(days=n)),
        (r'(\d+)\s+week[s]?\s+ago',  "week",  lambda n: scraped_at - timedelta(weeks=n)),
        (r'(\d+)\s+month[s]?\s+ago', "month", lambda n: scraped_at - timedelta(days=n * 30)),
        (r'(\d+)\s+year[s]?\s+ago',  "year",  lambda n: scraped_at.replace(year=scraped_at.year - n)),
        (r'a\s+year\s+ago',          "year",  lambda _: scraped_at.replace(year=scraped_at.year - 1)),
        (r'a\s+month\s+ago',         "month", lambda _: scraped_at - timedelta(days=30)),
        (r'a\s+week\s+ago',          "week",  lambda _: scraped_at - timedelta(weeks=1)),
        (r'yesterday',               "day",   lambda _: scraped_at - timedelta(days=1)),
    ]

    for pattern, precision, calculate in patterns:
        match = re.search(pattern, clean, re.IGNORECASE)
        if match:
            n = int(match.group(1)) if match.lastindex else 1
            estimated = calculate(n)
            return {
                "estimated_date": estimated.strftime("%Y-%m-%d"),
                "precision":      precision,
            }

    return {"estimated_date": None, "precision": "unknown"}


def generate_review_hash(source_id: str, review: dict) -> str:
    """
    Generate hash for a review.
    Uses source_id + author + normalized_date + rating

    Args:
        source_id (str): Source ID
        review (dict): Review data

    Returns:
        str: Review hash
    """

    author = review.get("_author_hash_only", "")
    normalized_date = normalize_date(review["date_raw"])
    raw = f"{source_id}|{author}|{normalized_date}|{review['rating']}"

    return hashlib.sha256(raw.encode()).hexdigest()
