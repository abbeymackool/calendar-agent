"""
Script: airbnb_booking
Purpose: Quick one-off to post a single Airbnb booking (useful for tests).

Data Shapes:
- Booking (core.types.Booking)
"""

from __future__ import annotations

from calendar_agent.config import settings
from calendar_agent.sync.run_airbnb import sync
from calendar_agent.utils.logging import setup_logging


def run():
    setup_logging(settings.log_level)

    # TODO: Replace with argparse/CLI flags if you want real inputs
    ex = [
        # Booking(source="airbnb", guest_name="Example", check_in=datetime(...), check_out=datetime(...), location="Disco")
    ]
    if not ex:
        print("airbnb_booking: populate the Booking example above or add CLI args.")
        return

    sync(ex)


if __name__ == "__main__":
    run()
