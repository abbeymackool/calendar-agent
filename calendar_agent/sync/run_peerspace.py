"""
actions/peerspace_to_disco.py
-------------------------------------------------
Handles Peerspace bookings by:
1. Adding setup/cleanup buffers to the Disco Bookings calendar.
2. Creating or updating all-day block events on the Airbnb calendar.
3. Merging block titles intelligently when multiple bookings share a day
   (e.g., "EVENT + SHOOT" or "2X SHOOTS").

Usage:
    python3 -m actions.peerspace_to_disco <BOOKING_ID> <EVENT|PHOTOSHOOT> <START_ISO> <END_ISO> [-v]

Example:
    python3 -m actions.peerspace_to_disco PS-TEST-20251129 PHOTOSHOOT 2025-11-29T19:00:00-05:00 2025-11-29T22:00:00-05:00
"""

import sys
from datetime import timedelta as TD
from dateutil import parser as dtp
from tools.gcal_tool import (
    get_cal_id,
    upsert_or_modify_buffer,
    upsert_or_attach_all_day,
    get_event_by_date,
    update_event_summary,
)
from tools.rules import block_dates_for_event

# ---------------------------------------------------------------------------
# GLOBAL CONSTANTS
# ---------------------------------------------------------------------------

CAL_DISCO = "Disco Bookings"      # writable calendar for events
CAL_BLOCK = "Block on Airbnb"     # all-day Airbnb availability blocks
TZ = "America/Detroit"            # local timezone

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def _merge_block_title(existing_title: str, new_label: str) -> str:
    """
    Merge an existing block title with a new label intelligently.

    Examples:
        "EVENT" + "SHOOT"      → "EVENT + SHOOT"
        "EVENT + SHOOT" + "SHOOT" → "EVENT + 2X SHOOTS"
        "2X SHOOTS" + "EVENT"  → "EVENT + 2X SHOOTS"
    """
    old_title = (existing_title or "").upper()
    new_label = new_label.upper()

    # Normalize "AM EVENT" → "EVENT"
    if " " in new_label:
        new_label = new_label.split()[-1]

    # Split into unique tokens like ["EVENT", "SHOOT"]
    tokens = [t.strip() for t in old_title.replace("×", "X").split("+") if t.strip()]
    base_counts = {}
    for t in tokens:
        # detect patterns like "2X SHOOTS"
        parts = t.split()
        if len(parts) >= 2 and parts[0].endswith("X"):
            try:
                n = int(parts[0].replace("X", ""))
                label = parts[1].rstrip("S")
                base_counts[label] = base_counts.get(label, 0) + n
            except Exception:
                base_counts[t.rstrip("S")] = base_counts.get(t.rstrip("S"), 1)
        else:
            base_counts[t.rstrip("S")] = base_counts.get(t.rstrip("S"), 1)

    # Add the new label
    label = new_label.rstrip("S")
    base_counts[label] = base_counts.get(label, 0) + 1

    # Build a clean merged title
    parts = []
    for k in sorted(base_counts):
        count = base_counts[k]
        if count == 1:
            parts.append(k)
        else:
            parts.append(f"{count}X {k}S")
    return " + ".join(parts)

# ---------------------------------------------------------------------------
# CORE LOGIC
# ---------------------------------------------------------------------------

def run(booking_id: str, kind: str, start_iso: str, end_iso: str, verbose=False):
    """
    Main entry point to handle a Peerspace booking.

    Args:
        booking_id: unique identifier for this booking.
        kind: "EVENT" or "PHOTOSHOOT".
        start_iso / end_iso: ISO-format local timestamps.
        verbose: if True, prints each action to stdout.
    """
    start = dtp.isoparse(start_iso)
    end = dtp.isoparse(end_iso)
    kind = kind.upper().strip()

    # Buffer durations per spec
    if kind == "EVENT":
        buf_start = start - TD(hours=1)
        buf_end = end + TD(hours=2)
    else:  # PHOTOSHOOT
        buf_start = start - TD(hours=1)
        buf_end = end + TD(hours=1)

    booking_key = f"ps|{booking_id}|{start.date()}"

    # 1️⃣ Create or update the setup/cleanup buffer on the Disco calendar
    upsert_or_modify_buffer(
        get_cal_id(CAL_DISCO),
        summary=kind,
        location="1-hr buffer",
        desired_start=buf_start,
        desired_end=buf_end,
        booking_key=booking_key,
        tz=TZ,
    )
    if verbose:
        print(f"[Disco] Added/updated {kind} buffer {buf_start} → {buf_end}")

    # 2️⃣ Handle the Airbnb block(s)
    cal_id = get_cal_id(CAL_BLOCK)

    # We still compute candidate dates via rules, but we may SKIP the prior day.
    candidate_dates = sorted(block_dates_for_event(start, end))

    # Turnover math
    two_hr_buffer_start = start - TD(hours=2)  # Airbnb turnover requirement
    starts_before_1pm = start.hour < 13        # Only < 1pm can ever require a prior-day AM block
    pushes_into_checkout = two_hr_buffer_start.hour < 11  # STRICT: 11:00 is OK; earlier overlaps checkout

    for d in candidate_dates:
        is_prev = (dtp.isoparse(d).date() == (start.date() - TD(days=1)))

        # Skip prior-day block unless BOTH conditions are met
        requires_am_block = is_prev and starts_before_1pm and pushes_into_checkout
        if is_prev and not requires_am_block:
            if verbose:
                print(f"[Block] Skipped prior-day block {d} (start {start.time()} satisfies 2h turnover)")
            continue

        block_title = f"AM {kind}" if requires_am_block else kind

        priv = {
            "managedBy": "CalendarAgent",
            "type": "AirbnbBlock",
            "booking_key": booking_key,
            "block_date": d,
            "ps_block_key": f"{booking_key}|{d}",
        }

        existing = get_event_by_date(cal_id, d)
        if existing:
            merged_title = _merge_block_title(existing.get("summary", ""), block_title)
            update_event_summary(cal_id, existing["id"], merged_title)
            if verbose:
                print(f"[Block] Updated {d}: {existing.get('summary')} → {merged_title}")
        else:
            upsert_or_attach_all_day(cal_id, summary=block_title, date_str=d, private_keys=priv)
            if verbose:
                print(f"[Block] Created new block {block_title} on {d}")

# ---------------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 4:
        print("Usage: python3 -m actions.peerspace_to_disco <BOOKING_ID> <EVENT|PHOTOSHOOT> <START_ISO> <END_ISO> [-v]")
        sys.exit(1)

    booking_id, kind, start_iso, end_iso = args[:4]
    verbose = ("-v" in args or "--verbose" in args)
    run(booking_id, kind, start_iso, end_iso, verbose=verbose)