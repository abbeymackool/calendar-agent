from dateutil import parser as dtp
from tools.gcal_tool import get_cal_id, upsert_event

DISCO = "Disco Bookings"  # writable Google calendar

def run(booking_id, guest, checkin_iso, checkout_iso):
    disco_id = get_cal_id(DISCO)
    ci = dtp.isoparse(checkin_iso)
    co = dtp.isoparse(checkout_iso)

    events = [
        ("ab_res", {"summary": f"{guest}",
                    "start": {"dateTime": ci.isoformat()},
                    "end":   {"dateTime": co.isoformat()}}),
        ("ab_checkin_buffer", {"summary": "CHECK-IN BUFFER",
                               "start": {"dateTime": (ci.replace()) .isoformat()},
                               "end":   {"dateTime": ci.isoformat()}}),
        ("ab_turnover", {"summary": "TURNOVER",
                         "start": {"dateTime": co.isoformat()},
                         "end":   {"dateTime": (co.replace()).isoformat()}}),
    ]
    # adjust buffer lengths: check-in buffer = 2h before; turnover = +2h
    from datetime import timedelta
    events[1][1]["start"]["dateTime"] = (ci - timedelta(hours=2)).isoformat()
    events[2][1]["end"]["dateTime"]   = (co + timedelta(hours=2)).isoformat()

    for type_key, body in events:
        body.setdefault("extendedProperties", {}).setdefault("private", {}).update(
            {"source":"agent","type":type_key,"booking_id":booking_id}
        )
        # composite key ensures a single event per type per booking
        upsert_event(disco_id, body, "type_booking", f"{type_key}|{booking_id}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        print('Usage: python -m actions.airbnb_to_disco <booking_id> "<guest name>" <checkin_iso> <checkout_iso>')
        sys.exit(1)
    run(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])