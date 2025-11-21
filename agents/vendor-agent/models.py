from pydantic import BaseModel
from typing import List
from datetime import datetime

class CreateListingPayload(BaseModel):
    vendor_id: str
    price: float
    location: str
    media_files: List[str]
    raw_tags: List[str] = []
    title: str | None = None
    description: str | None = None

class CreateEventPayload(BaseModel):
    agency_id: str
    title: str
    datetime: datetime
    location: str
    price: float
    media_files: List[str]
    raw_tags: List[str] = []
