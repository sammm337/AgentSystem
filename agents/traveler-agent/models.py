from pydantic import BaseModel
from typing import Optional, Dict, Any

class SearchRequest(BaseModel):
    query: str
    mode: str  # "via_vendor" | "via_agency"
    filters: Optional[Dict[str, Any]] = {}
    user_id: Optional[str] = None

class RecommendRequest(BaseModel):
    user_id: str
    limit: int = 5

class ItineraryRequest(BaseModel):
    user_id: str
    items: list  # list of listing/event IDs
    days: int = 1

class MessageRequest(BaseModel):
    user_id: str
    target_id: str
    message_type: str  # negotiation, booking, etc.
    context: Optional[str] = None
