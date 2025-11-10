import sys
from tools.gcal_tool import get_cal_id, delete_all_events_by_private
CAL_DISCO = "Disco Bookings"
CAL_BLOCK = "Block on Airbnb"

def run(booking_key: str):
    did = get_cal_id(CAL_DISCO)
    bid = get_cal_id(CAL_BLOCK)
    n1 = delete_all_events_by_private(did, "booking_key", booking_key)
    n2 = delete_all_events_by_private(bid, "booking_key", booking_key)
    # also remove per-day ps_block_key entries on Block on Airbnb
    # (they all start with booking_key + "|")
    from tools.gcal_tool import delete_events_by_private_prefix
    n3 = delete_events_by_private_prefix(bid, "ps_block_key", booking_key + "|")
    print(f"Removed {n1} from Disco, {n2+n3} from Block on Airbnb")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m actions.cleanup_booking 'ps|<Guest>|<YYYY-MM-DD>'")
        sys.exit(1)
    run(sys.argv[1])
