from datetime import datetime, timedelta
import sys, re
from tools.gcal_tool import get_cal_id, _svc

def run(calendar_name, title_substring, start_date, end_date):
    cal_id = get_cal_id(calendar_name)
    s = _svc()

    # window: whole days [start_date, end_date]
    d0 = datetime.strptime(start_date, "%Y-%m-%d")
    d1 = datetime.strptime(end_date,   "%Y-%m-%d") + timedelta(days=1)

    resp = s.events().list(
        calendarId=cal_id,
        timeMin=d0.astimezone().isoformat(),
        timeMax=d1.astimezone().isoformat(),
        singleEvents=True,
        maxResults=2500,
        orderBy="startTime",
    ).execute()

    needle = title_substring.lower()
    deleted = 0
    for e in resp.get("items", []):
        title = e.get("summary","")
        if needle in title.lower():
            s.events().delete(calendarId=cal_id, eventId=e["id"]).execute()
            print(f"Deleted: {title}")
            deleted += 1
    if deleted == 0:
        print("No matching events found.")

if __name__ == "__main__":
    # Usage: python -m actions.cancel_by_title "Upstairs Bookings" "Brandon" 2025-12-20 2025-12-23
    if len(sys.argv) != 5:
        print('Usage: python -m actions.cancel_by_title "<Calendar Name>" "<Title contains>" YYYY-MM-DD YYYY-MM-DD')
        sys.exit(1)
    run(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])