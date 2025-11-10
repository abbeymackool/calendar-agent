import sys
from datetime import datetime, timedelta
from tools.gcal_tool import get_cal_id, _svc

def iso(dt): return dt.isoformat()

def list_events(cal_name, start_iso, end_iso):
    cal_id = get_cal_id(cal_name)
    s = _svc()
    resp = s.events().list(calendarId=cal_id, timeMin=start_iso, timeMax=end_iso,
                           singleEvents=True, maxResults=2500).execute()
    items = resp.get("items", []) or []
    print(f"\n=== {cal_name} ({len(items)} events) ===")
    for e in items:
        summ = e.get("summary","")
        eid = e.get("id","")
        start = e.get("start",{}); end = e.get("end",{})
        priv = e.get("extendedProperties",{}).get("private",{})
        print(f"- {summ}  id={eid}")
        print(f"  start={start}  end={end}")
        print(f"  private={priv}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python -m actions.debug_list '<Calendar Name>' YYYY-MM-DD YYYY-MM-DD")
        sys.exit(1)
    cal_name, d1, d2 = sys.argv[1], sys.argv[2], sys.argv[3]
    # include entire end day
    start_iso = datetime.fromisoformat(d1).replace(hour=0, minute=0, second=0, microsecond=0).astimezone().isoformat()
    end_iso   = (datetime.fromisoformat(d2) + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).astimezone().isoformat()
    list_events(cal_name, start_iso, end_iso)
