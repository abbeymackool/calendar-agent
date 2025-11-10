from tools.gcal_tool import get_cal_id, delete_event_by_private

DISCO = "Disco Bookings"
UPSTAIRS = "Upstairs Bookings"
BLOCK = "Block on Airbnb"

def cancel_all_for_booking(booking_id, listing):
    if listing == "disco":
        cal_ids = [get_cal_id(DISCO), get_cal_id(BLOCK)]
        # Disco: three Airbnb types + Peerspace buffer; Block calendar: daily blocks
        keys = [
            ("type_booking", f"ab_res|{booking_id}"),
            ("type_booking", f"ab_checkin_buffer|{booking_id}"),
            ("type_booking", f"ab_turnover|{booking_id}"),
            ("ps_booking", booking_id)  # Peerspace 1-hr buffer
        ]
        # Block-on-Airbnb: composite keys ps_block_key "<booking_id>|<YYYY-MM-DD>"
        # we don't know dates; try generic "booking_id"
        extra_key = ("booking_id", booking_id)
    elif listing == "upstairs":
        cal_ids = [get_cal_id(UPSTAIRS)]
        keys = [("type_booking", f"ab_res|{booking_id}")]
        extra_key = None
    else:
        raise SystemExit("listing must be 'disco' or 'upstairs'")

    # delete by known keys
    for cal_id in cal_ids:
        for k, v in keys:
            delete_event_by_private(cal_id, k, v)
        if extra_key:
            delete_event_by_private(cal_id, extra_key[0], extra_key[1])

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python -m actions.cancel <booking_id> <disco|upstairs>")
        sys.exit(1)
    cancel_all_for_booking(sys.argv[1], sys.argv[2])