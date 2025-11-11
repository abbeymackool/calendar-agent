"""
Script: actions.debug_list
Purpose: List events between two dates on a named calendar to validate syncs.

Usage:
    python -m actions.debug_list "Disco Bookings" 2025-11-30 2025-12-02
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Dict

from calendar_agent.core.types import CalendarRef
from calendar_agent.calendar.google import list_between
from calendar_agent.config import settings
from calendar_agent.utils.logging import setup_logging


NAME_TO_ID: Dict[str, str] = {
    "Disco Bookings": settings.CAL_DISCO_BOOKINGS,
    "Upstairs Bookings": settings.CAL_UPSTAIRS_BOOKINGS,
    "Block on Airbnb": settings.CAL_BLOCK_ON_AIRBNB,
}


def parse_date(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def main():
    if len(sys.argv) != 4:
        print("Usage: python -m actions.debug_list \"<Calendar Name>\" YYYY-MM-DD YYYY-MM-DD")
        sys.exit(2)

    cal_name = sys.argv[1]
    start = parse_date(sys.argv[2])
    end = parse_date(sys.argv[3])

    setup_logging("INFO")

    cal_id = NAME_TO_ID.get(cal_name)
    if not cal_id:
        print(f"Unknown calendar name: {cal_name}")
        sys.exit(1)

    cal = CalendarRef(name=cal_name, calendar_id=cal_id)
    any_printed = False
    for ev in list_between(cal, start, end):
        any_printed = True
        start_dt = ev.get("start", {}).get("dateTime", "?")
        end_dt = ev.get("end", {}).get("dateTime", "?")
        print(f"- {ev.get('summary','(no title)')} | {start_dt} -> {end_dt} | id={ev.get('id')}")
    if not any_printed:
        print("(no events)")
    print("Done.")


if __name__ == "__main__":
    main()
