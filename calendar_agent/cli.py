"""
Calendar Agent CLI
Now with compact, professional output and buffer-aware Airbnb bookings.
"""

from __future__ import annotations

import typer
from rich import print
from datetime import datetime
from zoneinfo import ZoneInfo
import traceback
import sys

from calendar_agent.config import settings
from calendar_agent.utils.logging import setup_logging
from calendar_agent.core.types import Booking, CalendarRef
from calendar_agent.sync.run_airbnb import sync as sync_bookings
from calendar_agent.calendar.google import create_event

app = typer.Typer(add_completion=False, help="Calendar Agent — unified CLI")
tz = ZoneInfo("America/Detroit")


def _handle_error(err: Exception, debug: bool = False):
    if debug:
        traceback.print_exc()
    else:
        print(f"[red]✗ {type(err).__name__}: {err}[/red]")
    sys.exit(1)


@app.command("airbnb")
def cmd_airbnb(
    guest: str = typer.Option(..., "--guest", help="Guest name"),
    loc: str = typer.Option(..., "--loc", help="Location: disco | upstairs"),
    in_: str = typer.Option(..., "--in", help="Check-in datetime, e.g. 2025-12-03T16:00"),
    out: str = typer.Option(..., "--out", help="Checkout datetime, e.g. 2025-12-04T11:00"),
    notes: str = typer.Option("", "--notes", help="Optional notes"),
    debug: bool = typer.Option(False, "--debug", help="Show full traceback"),
):
    """Create an Airbnb booking event (with automatic buffers)."""
    setup_logging(settings.LOG_LEVEL)
    try:
        loc_norm = loc.strip().lower()
        if loc_norm not in {"disco", "upstairs"}:
            raise ValueError(f"Invalid --loc: {loc} (use disco|upstairs)")

        booking = Booking(
            source="airbnb",
            guest_name=guest.title(),
            check_in=datetime.fromisoformat(in_).replace(tzinfo=tz),
            check_out=datetime.fromisoformat(out).replace(tzinfo=tz),
            location="Disco" if loc_norm == "disco" else "Upstairs",
            notes=notes,
        )

        counts = sync_bookings([booking])
        # Compact “Disco Bookings – 1 event added” style summary
        disco = counts.get("Disco Bookings", 0)
        up = counts.get("Upstairs Bookings", 0)
        blk = counts.get("Block on Airbnb", 0)
        parts = []
        if disco:
            parts.append(f"Disco Bookings – {disco} event{'s' if disco != 1 else ''} added")
        if up:
            parts.append(f"Upstairs Bookings – {up} event{'s' if up != 1 else ''} added")
        if blk:
            parts.append(f"Block on Airbnb – {blk} event{'s' if blk != 1 else ''} added")
        print("[green]✓[/green] " + " | ".join(parts))

    except Exception as e:
        _handle_error(e, debug)


@app.command("event")
def cmd_event(
    guest: str = typer.Option(..., "--guest", help="Client/contact name"),
    loc: str = typer.Option(..., "--loc", help="Location: disco | upstairs"),
    in_: str = typer.Option(..., "--in", help="Start datetime"),
    out: str = typer.Option(..., "--out", help="End datetime"),
    title: str = typer.Option(..., "--title", help="Event title"),
    debug: bool = typer.Option(False, "--debug", help="Show full traceback"),
):
    """Create a Block/Event (goes to Block on Airbnb calendar)."""
    setup_logging(settings.LOG_LEVEL)
    try:
        start = datetime.fromisoformat(in_).replace(tzinfo=tz)
        end = datetime.fromisoformat(out).replace(tzinfo=tz)

        cal = CalendarRef(name="Block on Airbnb", calendar_id=settings.CAL_BLOCK_ON_AIRBNB)
        desc = f"{title} — {guest.title()}"
        event_id = create_event(cal, summary=desc, start=start, end=end, description=desc)

        print(f"[green]✓[/green] Block on Airbnb – 1 event added")
        print(f"  • {title} for {guest.title()} ({loc.capitalize()})  {start:%Y-%m-%d %H:%M} → {end:%Y-%m-%d %H:%M}")
        print(f"  • Event ID: {event_id}")
    except Exception as e:
        _handle_error(e, debug)


@app.command("env")
def cmd_env():
    """Display loaded environment variables."""
    print("[bold cyan]Loaded environment variables:[/bold cyan]")
    for k, v in settings.as_safe_dict().items():
        print(f"  {k} = {v}")


def main():
    app()


if __name__ == "__main__":
    main()
