import sys
from datetime import datetime, timedelta

from tools.gcal_tool import get_cal_id, upsert_event

BLOCK = "Block on Airbnb"  # must match the exact calendar name in Google


def run(title, *dates):
    block_id = get_cal_id(BLOCK)
    for d in dates:
        day = datetime.strptime(d, "%Y-%m-%d").date()
        next_day = (day + timedelta(days=1)).isoformat()
        body = {
            "summary": title,
            "start": {"date": day.isoformat()},
            "end": {"date": next_day},
        }
        upsert_event(block_id, body, "manual_block", f"{title}-{d}")
        print(f"Added all-day block on {d} ({title})")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m actions.block_manual EVENT 2025-12-27 2025-12-28")
        sys.exit(1)
    run(sys.argv[1], *sys.argv[2:])
