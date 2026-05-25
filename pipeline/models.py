from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ScrapeConfig(BaseModel):
    delay_seconds: int = 5
    max_retries: int = 3

class ClientSource(BaseModel):
    source_id: int
    client_id: str
    client_name: str
    platform: str
    url: str
    active: bool
    scrape_config: ScrapeConfig = ScrapeConfig()

class PipelineRun(BaseModel):
    client_id: str
    source_id: str
    status: str
    started_at: datetime
    finished_at: datetime
    reviews_extracted: int = 0
    anomaly_flag: bool = False
    anomaly_reason: Optional[str] = None
    error_message: Optional[str] = None
