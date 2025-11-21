# shared/schemas/event_schema.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MediaItem(BaseModel):
    path: str
    kind: str
    tags: Optional[List[str]] = []

class Event(BaseModel):
    id: Optional[str] = None
    agency_id: str
    title: str
    description: str
    datetime: datetime
    location: str
    price: float
    tags: List[str] = []
    media: List[MediaItem] = []
    created_at: Optional[datetime] = None
    type: str = Field(default="event", const=True)
