"""Database utils for pipeline"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pipeline.models import ClientSource, PipelineRun
from scrapers.google_maps_utils import generate_review_hash

load_dotenv()

def get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


def load_active_sources() -> list[ClientSource]:
    """Load all active client sources from database."""
    db_client = get_client()

    result = (
        db_client.table("rr_clients_sources")
        .select("*, rr_clients(client_name, status)")
        .eq("active", True)
        .eq("rr_clients.status", 1)
        .eq("platform", "google_maps")
        .execute()
    )

    rows = []
    for row in result.data:
        nested = row.pop("rr_clients", {})
        row["client_name"] = nested.get("client_name")
        rows.append(ClientSource(**row))

    return [ClientSource(**row) for row in result.data]


def save_pipeline_run(run: PipelineRun) -> None:
    db_client = get_client()

    db_client.table("rr_pipeline_runs").insert({
        "client_id":         run.client_id,
        "source_id":         run.source_id,
        "status":            run.status,
        "started_at":        run.started_at.isoformat(),
        "finished_at":       run.finished_at.isoformat(),
        "reviews_extracted": run.reviews_extracted,
        "anomaly_flag":      run.anomaly_flag,
        "anomaly_reason":    run.anomaly_reason,
        "error_message":     run.error_message,
    }).execute()


def save_google_maps_reviews(reviews: list[dict], source_id: str, client_id: str) -> dict:
    """Save google maps reviews to database"""

    rows = []
    db_client = get_client()

    for r in reviews:
        review_hash = generate_review_hash(
            source_id=source_id,
            review=r
        )
        rows.append({
            "source_id":    source_id,
            "client_id":    client_id,
            "review_text":  r["review"],
            "rating":       r["rating"],
            "review_date":  r["date"],
            "review_hash":  review_hash,
            "metadata":     {"likes": r.get("likes", 0)}
        })

    result = (
        db_client.table("rr_reviews")
        .upsert(rows, on_conflict="review_hash")
        .execute()
    )
    return result
