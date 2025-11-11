from datetime import datetime

from pydantic import BaseModel


class CalendarEvent(BaseModel):
    uid: str
    summary: str
    description: str
    start: datetime
    end: datetime
    calendar_id: str
    source: str
    source_external_id: str
    location: str | None = None
