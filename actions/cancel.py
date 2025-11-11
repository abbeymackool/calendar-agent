"""
actions/cancel.py
-------------------------------------------------
Cancels and removes calendar events for a given Airbnb or Peerspace booking.

Responsibilities:
1. Deletes all related events from the relevant calendars (Disco, Upstairs, and/or Block on Airbnb).
2. Uses extendedProperties.private keys to target events precisely without disturbing unrelated items.
3. Supports both Airbnb and Peerspace bookings with appropriate key types.

Usage:
    python3 -m actions.cancel <BOOKING_ID> <disco|upstairs>

Examples:
    python3 -m actions.cancel AB-TEST-DISCO-SARAH-20251202 disco
    python3 -m actions.cancel AB-TEST-UPSTAIRS-GREG-20251130 upstairs
"""

import sys

from tools.gcal_tool import delete_event_by_private, get_cal_id

# ---------------------------------------------------------------------------
# GLOBAL CALENDAR IDENTIFIERS
# ---------------------------------------------------------------------------

CAL_DISCO = "Disco Bookings"  # Main floor space (Airbnb + Peerspace)
CAL_UPSTAIRS = "Upstairs Bookings"  # Second-floor Airbnb listing
CAL_BLOCK = "Block on Airbnb"  # All-day availability blocks for both listings

# ---------------------------------------------------------------------------
# CORE FUNCTION
# ---------------------------------------------------------------------------


def cancel_all_for_booking(booking_id: str, listing: str, verbose: bool = True) -> None:
    """
    Deletes all events associated with a given booking ID across relevant calendars.

    Args:
        booking_id: The unique booking identifier (e.g. AB-1234 or PS-TEST-20251201).
        listing: "disco" or "upstairs" to determine which calendars to clean.
        verbose: If True, prints actions taken to the console.

    Behavior:
        - For 'disco':
            Removes Airbnb reservation, buffers, turnover, and any Peerspace buffer or block events.
        - For 'upstairs':
            Removes Airbnb reservations from the Upstairs calendar only.
    """

    # ------------------------------
    # Calendar + key selection
    # ------------------------------
    if listing.lower() == "disco":
        cal_ids = [get_cal_id(CAL_DISCO), get_cal_id(CAL_BLOCK)]

        # These are the known extendedProperties keys for Disco-related events
        keys = [
            ("type_booking", f"ab_res|{booking_id}"),  # main Airbnb booking
            ("type_booking", f"ab_checkin_buffer|{booking_id}"),  # check-in buffer
            ("type_booking", f"ab_turnover|{booking_id}"),  # turnover buffer
            ("ps_booking", booking_id),  # Peerspace 1-hour buffer
        ]

        # Some events (especially Blocks) use generic "booking_id"
        extra_key = ("booking_id", booking_id)

    elif listing.lower() == "upstairs":
        cal_ids = [get_cal_id(CAL_UPSTAIRS)]
        keys = [("type_booking", f"ab_res|{booking_id}")]
        extra_key = None

    else:
        raise SystemExit("Error: listing must be 'disco' or 'upstairs'.")

    # ------------------------------
    # Deletion process
    # ------------------------------
    for cal_id in cal_ids:
        for key, value in keys:
            count = delete_event_by_private(cal_id, key, value)
            if verbose and count:
                print(f"[{listing.upper()}] Deleted {count} events where {key}='{value}'")

        if extra_key:
            count = delete_event_by_private(cal_id, extra_key[0], extra_key[1])
            if verbose and count:
                print(
                    f"[{listing.upper()}] Deleted {count} events where {extra_key[0]}='{extra_key[1]}'"
                )

    if verbose:
        print(f"[{listing.upper()}] Cancellation complete for booking_id={booking_id}")


# ---------------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage: python3 -m actions.cancel <BOOKING_ID> <disco|upstairs>")
        sys.exit(1)

    booking_id, listing = args[:2]
    cancel_all_for_booking(booking_id, listing, verbose=True)
