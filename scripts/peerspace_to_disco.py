"""
Script: peerspace_to_disco
Purpose: Convert Peerspace bookings to Disco calendar events.

Data Shapes:
- Booking (core.types.Booking)
"""

from __future__ import annotations

from calendar_agent.config import settings
from calendar_agent.sync.run_airbnb import sync as sync_bookings
from calendar_agent.utils.logging import setup_logging


def run():
    setup_logging(settings.log_level)

    # TODO: Replace with real ingestion (CSV/API)
    demo = [
        # Booking(source="peerspace", guest_name="ProdTeam", check_in=datetime(...), check_out=datetime(...), location="Disco", notes="Photoshoot")
    ]
    if not demo:
        print("peerspace_to_disco: no input yet — wire your ingestion.")
        return

    sync_bookings(demo)


if __name__ == "__main__":
    run()
