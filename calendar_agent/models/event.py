from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CalendarEvent(BaseModel):
    uid: str
    summary: str
    description: str
    start: datetime
    end: datetime
    calendar_id: str
    source: str
    source_external_id: str
    location: Optional[str] = None
