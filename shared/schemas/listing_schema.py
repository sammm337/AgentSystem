from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from typing import Literal

class MediaItem(BaseModel):
    path: str
    kind: str  # 'audio'/'image'/'video'
    tags: Optional[List[str]] = []

class ListingBase(BaseModel):
    id: Optional[str] = None
    vendor_id: str
    title: str
    description: str
    price: float
    location: str
    tags: List[str] = []
    media: List[MediaItem] = []
    created_at: Optional[datetime] = None
    type: Literal["listing"] = "listing"

class EventBase(BaseModel):
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
    type: Literal["event"] = "event"
