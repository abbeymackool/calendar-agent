from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Booking(BaseModel):
    source: Literal["airbnb", "peerspace", "gmail"]
    external_id: str
    space: Literal["Disco", "Upstairs"]
    kind: Literal["lodging", "event", "production"]
    start: datetime
    end: datetime
    guest_name: str | None = None
    notes: str | None = None
    raw: dict = {}
