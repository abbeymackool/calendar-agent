from dateutil import parser as dtp

from tools.gcal_tool import get_cal_id, upsert_event

UPSTAIRS = "Upstairs Bookings"
TZ = "America/Detroit"


def run(booking_id, guest, checkin_iso, checkout_iso):
    up_id = get_cal_id(UPSTAIRS)
    ci = dtp.isoparse(checkin_iso)
    co = dtp.isoparse(checkout_iso)

    body = {
        "summary": f"{guest}",
        "start": {"dateTime": ci.isoformat(), "timeZone": TZ},
        "end": {"dateTime": co.isoformat(), "timeZone": TZ},
        "extendedProperties": {
            "private": {"source": "agent", "type": "ab_res", "booking_id": booking_id}
        },
    }
    upsert_event(up_id, body, "type_booking", f"ab_res|{booking_id}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 5:
        print(
            'Usage: python -m actions.airbnb_to_upstairs <booking_id> "<guest name>" <checkin_iso> <checkout_iso>'
        )
        sys.exit(1)
    run(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
