from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Optional

class Booking(BaseModel):
    source: Literal["airbnb","peerspace","gmail"]
    external_id: str
    space: Literal["Disco","Upstairs"]
    kind: Literal["lodging","event","production"]
    start: datetime
    end: datetime
    guest_name: Optional[str] = None
    notes: Optional[str] = None
    raw: dict = {}
