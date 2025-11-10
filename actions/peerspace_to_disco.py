# actions/peerspace_to_disco.py
import sys
from datetime import timedelta as TD
from dateutil import parser as dtp

from tools.gcal_tool import get_cal_id, upsert_or_modify_buffer, upsert_or_attach_all_day
from tools.rules import block_dates_for_event

CAL_DISCO = "Disco Bookings"
CAL_BLOCK = "Block on Airbnb"
TZ = "America/Detroit"

def run(booking_id: str, kind: str, start_iso: str, end_iso: str):
    """
    booking_id: any identifier for this Peerspace booking (e.g., PS-TEST-2025-12-01)
    kind: EVENT | PHOTOSHOOT
    start_iso/end_iso: e.g., 2025-12-01T12:30:00-05:00
    """
    start = dtp.isoparse(start_iso)
    end   = dtp.isoparse(end_iso)

    # Buffer durations per spec
    if kind.upper() == "EVENT":
        buf_start = start - TD(hours=1)
        buf_end   = end   + TD(hours=2)
        base_title = "EVENT"
    else:
        buf_start = start - TD(hours=1)
        buf_end   = end   + TD(hours=1)
        base_title = "PHOTOSHOOT"

    # Use the unified key going forward
    booking_key = f"ps|{booking_id}|{start.date()}"

    # 1) Disco buffer: adopt/patch or insert
    upsert_or_modify_buffer(
        get_cal_id(CAL_DISCO),
        summary=base_title,
        location="1-hr buffer",
        desired_start=buf_start,
        desired_end=buf_end,
        booking_key=booking_key,
        tz=TZ,
    )

    # 2) Airbnb all-day blocks (adopt or insert); AM label if prev day & start < 1pm
    for d in sorted(block_dates_for_event(start, end)):
        is_prev = (dtp.isoparse(d).date() == (start.date() - TD(days=1)))
        starts_before_1pm = start.hour < 13
        block_title = f"AM {base_title}" if (is_prev and starts_before_1pm) else base_title

        priv = {
            "managedBy": "CalendarAgent",
            "type": "AirbnbBlock",
            "booking_key": booking_key,
            "block_date": d,
            "ps_block_key": f"{booking_key}|{d}",
        }
        upsert_or_attach_all_day(get_cal_id(CAL_BLOCK), summary=block_title, date_str=d, private_keys=priv)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python -m actions.peerspace_to_disco <BOOKING_ID> <EVENT|PHOTOSHOOT> <START_ISO> <END_ISO>")
        sys.exit(1)
    run(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])