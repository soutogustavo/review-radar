"""Pipeline (extra) tasks"""

import logging
from prefect import task
from datetime import datetime

from pipeline.models import ClientSource
from pipeline.db import save_pipeline_run
from pipeline.models import PipelineRun

logging.root.setLevel(logging.INFO)
logger = logging.getLogger("Pipeline Tasks")


@task(name="save-run")
def save_run(
    run: ClientSource, reviews: list,
    anomaly: dict, started_at: datetime, error: str = None
):
    """This saves every pipeline run

    Args:
        run (ClientSource): Client source data
        reviews (list): List of reviews
        anomaly (dict): Anomaly data
        started_at (datetime): Start time
        error (str): Error message

    Returns:
        None
    """

    run = PipelineRun(
        client_id=run.client_id,
        source_id=run.source_id,
        status="failed" if error else "success",
        started_at=started_at,
        finished_at=datetime.utcnow(),
        reviews_extracted=len(reviews),
        anomaly_flag=anomaly.get("anomaly_flag") or False,
        anomaly_reason=anomaly.get("anomaly_reason") or None,
        error_message=error,
    )
    save_pipeline_run(run)
