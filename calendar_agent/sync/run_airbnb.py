"""
Module: sync.run_airbnb
Purpose: Create Airbnb booking events + automatic buffers.

Behavior per booking:
- Main event on the location's Bookings calendar (title = guest name).
- Check-in buffer: (check_in - 2h) -> check_in on "Block on Airbnb".
- Turnover buffer: check_out -> (check_out + 2h) on "Block on Airbnb".

Returns aggregate counts for compact CLI output.
"""

from __future__ import annotations

import logging
from typing import Iterable, Dict
from datetime import timedelta

from calendar_agent.config import settings
from calendar_agent.core.types import Booking, CalendarRef
from calendar_agent.calendar.google import create_event

LOGGER = logging.getLogger(__name__)


def _bookings_calendar_for(location: str) -> CalendarRef:
    """Map location to its Bookings calendar."""
    if location == "Disco":
        return CalendarRef(name="Disco Bookings", calendar_id=settings.CAL_DISCO_BOOKINGS)
    if location == "Upstairs":
        return CalendarRef(name="Upstairs Bookings", calendar_id=settings.CAL_UPSTAIRS_BOOKINGS)
    raise ValueError(f"Unknown location: {location}")


def _blocks_calendar() -> CalendarRef:
    """Single blocks calendar for all buffers/events."""
    return CalendarRef(name="Block on Airbnb", calendar_id=settings.CAL_BLOCK_ON_AIRBNB)


def _create_main_event(b: Booking) -> str:
    """Create the main booking event on the location's Bookings calendar."""
    cal = _bookings_calendar_for(b.location)
    title = b.guest_name.title()  # e.g., "Susan"
    desc = (b.notes or "").strip()
    return create_event(cal, summary=title, start=b.check_in, end=b.check_out, description=desc)


def _create_buffers(b: Booking) -> tuple[str, str]:
    """
    Create check-in and turnover buffers on the Block on Airbnb calendar.
    - Check-in buffer: [check_in - 2h, check_in]
    - Turnover buffer: [check_out, check_out + 2h]
    """
    blocks = _blocks_calendar()

    # Check-in buffer
    ci_start = b.check_in - timedelta(hours=2)
    ci_end = b.check_in
    ci_title = f"Check-in Buffer — {b.guest_name.title()} ({b.location})"
    ci_id = create_event(blocks, summary=ci_title, start=ci_start, end=ci_end, description=ci_title)

    # Turnover buffer
    to_start = b.check_out
    to_end = b.check_out + timedelta(hours=2)
    to_title = f"Turnover — {b.guest_name.title()} ({b.location})"
    to_id = create_event(blocks, summary=to_title, start=to_start, end=to_end, description=to_title)

    return ci_id, to_id


def sync(bookings: Iterable[Booking]) -> Dict[str, int]:
    """
    Sync a batch of bookings.
    Returns:
        counts: dict like {"Disco Bookings": 1, "Upstairs Bookings": 0, "Block on Airbnb": 2}
    """
    counts: Dict[str, int] = {"Disco Bookings": 0, "Upstairs Bookings": 0, "Block on Airbnb": 0}

    for b in bookings:
        main_id = _create_main_event(b)
        cal_name = "Disco Bookings" if b.location == "Disco" else "Upstairs Bookings"
        counts[cal_name] += 1
        LOGGER.info("Created main event %s on %s", main_id, cal_name)

        ci_id, to_id = _create_buffers(b)
        counts["Block on Airbnb"] += 2
        LOGGER.info("Created buffers %s, %s on Block on Airbnb", ci_id, to_id)

    LOGGER.info("Batch complete: %s", counts)
    return counts


def main() -> None:
    LOGGER.info("Run via CLI; no standalone main scenario here.")
