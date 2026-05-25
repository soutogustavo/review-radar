
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pipeline.models import ClientSource

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
