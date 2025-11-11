"""
Module: types
Purpose: Canonical data shapes used across the Calendar Agent.

Data Shapes:
- Booking: Airbnb/Peerspace booking window and metadata
- EventBlock: Generic calendar block (e.g., holds, shoots)
- CalendarRef: Canonical reference to a target calendar
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class CalendarRef(BaseModel):
    """Reference to a specific resource calendar."""
    name: str  # allow any calendar display name (e.g., "Block on Airbnb")
    provider: Literal["google"] = "google"
    calendar_id: str = Field(..., description="Google Calendar ID/email")


class Booking(BaseModel):
    """An Airbnb/Peerspace booking."""
    source: Literal["airbnb", "peerspace"]
    guest_name: str
    check_in: datetime
    check_out: datetime
    location: Literal["Disco", "Upstairs"]
    notes: Optional[str] = None


class EventBlock(BaseModel):
    """A generic event (production, photoshoot, manual hold)."""
    title: str
    start: datetime
    end: datetime
    location: Literal["Disco", "Upstairs"]
    description: Optional[str] = None
