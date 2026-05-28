"""Utils for google maps scraper"""

import re
import hashlib
import logging
from bs4 import BeautifulSoup, NavigableString
from datetime import datetime, timedelta
from prefect import task

logging.root.setLevel(logging.INFO)
logger = logging.getLogger("Google Maps Utils")


@task
def parse_maps_reviews_from_html(html: str, source_id: str) -> list[dict]:
    logger.info("Parsing reviews...")

    soup = BeautifulSoup(html, "html.parser")
    reviews = soup.find_all("div", class_="jftiEf")
    logger.info(f"HTML size: {len(html)} chars | jftiEf divs found: {len(reviews)}")
    scraped_at = datetime.utcnow()
    results    = []

    # temporary, only for debug
    with open(f"/tmp/debug_html_{source_id}.html", "w") as f:
        f.write(html)

    for review in reviews:

        # --- rating ---
        rating    = 0
        rating_el = review.find("span", class_="kvMYJc")
        if rating_el:
            match  = re.search(r"(\d+)", rating_el.get("aria-label", ""))
            rating = int(match.group(1)) if match else 0
        else:
            rating_el = review.find("span", class_="fzvQIb")
            if rating_el:
                try:
                    # "4/5" or "4.2/5" format → take only the numerator
                    rating = round(float(rating_el.get_text(strip=True).split("/")[0]))
                except ValueError:
                    rating = 0

        # --- review text ---
        text_el = review.find("span", class_="wiI7pd")

        # --- date ---
        date_raw = ""
        date_el  = review.find("span", class_="rsqaWe")
        if date_el:
            date_raw = date_el.get_text(strip=True)
        else:
            date_el = review.find("span", class_="xRkPPb")
            if date_el:
                # structure: NavigableString("X months ago on") + <span>icon</span>
                # take only the NavigableString and remove the " on" at the end
                first_text = next(
                    (str(c).strip() for c in date_el.children if isinstance(c, NavigableString)),
                    ""
                )
                date_raw = re.sub(r'\s+on\s*$', '', first_text).strip()

        # --- likes ---
        likes_el = review.find("span", class_="pkWtMe")

        # --- author (hash only, don't persist) ---
        author_el = review.find("div", class_="d4r55")
        author    = author_el.get_text(strip=True) if author_el else ""

        row = {
            "review":            text_el.get_text(strip=True) if text_el else "",
            "rating":            rating,
            "date_raw":          date_raw,
            **parse_relative_date(date_raw, scraped_at),
            "likes":             int(likes_el.get_text(strip=True))
                                 if likes_el and likes_el.get_text(strip=True).isdigit() else 0,
            "_author_hash_only": author,
        }
        row["review_hash"] = generate_review_hash(source_id, row)
        results.append(row)

    logger.info(f"Parsed/extracted {len(results)} reviews")
    return results


def normalize_date(date_str: str) -> str:
    return re.sub(r"^[Ee]dited\s+", "", date_str).strip()


def parse_relative_date(date_str: str, scraped_at: datetime = None) -> dict:
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
            n        = int(match.group(1)) if match.lastindex else 1
            estimated = calculate(n)
            return {"estimated_date": estimated.strftime("%Y-%m-%d"), "precision": precision}

    return {"estimated_date": None, "precision": "unknown"}


def generate_review_hash(source_id: str, review: dict) -> str:
    author          = review.get("_author_hash_only", "")
    normalized_date = normalize_date(review.get("date_raw", ""))
    rating          = review.get("rating", 0)
    text_snippet    = review.get("review", "")[:100]
    raw             = f"{source_id}|{author}|{normalized_date}|{rating}|{text_snippet}"
    return hashlib.sha256(raw.encode()).hexdigest()


def deduplicate_reviews(reviews: list[dict]) -> list[dict]:
    seen   = set()
    unique = []
    for review in reviews:
        h = review["review_hash"]
        if h not in seen:
            seen.add(h)
            unique.append(review)
    return unique
