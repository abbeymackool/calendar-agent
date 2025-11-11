# tools/rules.py
from datetime import datetime, time, timedelta

# --- Airbnb rules ---
AIRBNB_CHECKIN = time(16, 0)  # 4 PM
AIRBNB_CHECKOUT = time(11, 0)  # 11 AM
POST_EVENT_BUFFER_HOURS = 2  # minimum clean-up window after event/photoshoot


def block_dates_for_event(start_dt, end_dt):
    """
    Determine which Airbnb calendar dates should be blocked for an event or shoot.

    Rules:
      - Always block the *previous* day if any part of the booking happens before
        Airbnb’s standard 4 PM check-in.
      - Always block the *current* day if the booking ends late enough that,
        when you add a 2 hour buffer, it runs past 4 PM check-in.
      - Works across multi-day events.
    """
    blocks = set()
    local = start_dt.tzinfo
    cur = start_dt.date()
    last = (end_dt - timedelta(seconds=1)).date()

    while cur <= last:
        day_start = datetime.combine(cur, time(0, 0), tzinfo=local)
        day_end = datetime.combine(cur, time(23, 59, 59), tzinfo=local)

        seg_start = max(start_dt, day_start)
        seg_end = min(end_dt, day_end)

        # Block the previous day if the day starts before 4 PM
        if seg_start.time() < AIRBNB_CHECKIN:
            blocks.add((cur - timedelta(days=1)).isoformat())

        # Block the same day if end + 2 hr pad crosses 4 PM check-in
        cutoff = datetime.combine(cur, AIRBNB_CHECKIN, tzinfo=local)
        if (seg_end + timedelta(hours=POST_EVENT_BUFFER_HOURS)) > cutoff:
            blocks.add(cur.isoformat())

        cur += timedelta(days=1)

    return blocks


def one_hour_buffer_event(title, start_dt, end_dt):
    """
    Build a calendar event body that starts 1 hour before and ends 1 hour after
    the provided window, labeled with '1-hr buffer'.
    """
    return {
        "summary": title,
        "location": "1-hr buffer",
        "start": {"dateTime": (start_dt - timedelta(hours=1)).isoformat()},
        "end": {"dateTime": (end_dt + timedelta(hours=1)).isoformat()},
    }
