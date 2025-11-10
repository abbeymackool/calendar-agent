# actions/peerspace_cancel.py
import sys
from datetime import timedelta as TD
from dateutil import parser as dtp
from collections import Counter

from tools.gcal_tool import (
    get_cal_id, update_event_summary,
    find_all_day_event_on_date, delete_events_by_private
)
from tools.rules import block_dates_for_event

CAL_DISCO = "Disco Bookings"
CAL_BLOCK = "Block on Airbnb"

def _normalize_tokens(summary: str):
    s = (summary or "").upper().replace("×","X")
    parts = [p.strip() for p in s.split("+") if p.strip()]
    tokens = []
    for p in parts:
        bits = p.split()
        if len(bits) >= 2 and bits[0].endswith("X"):
            try:
                n = int(bits[0].replace("X",""))
                word = " ".join(bits[1:])
                if word.endswith("S"): word = word[:-1]
                tokens.extend([word] * n)
            except Exception:
                tokens.append(p.rstrip("S"))
        else:
            w = p
            if w.endswith("S"): w = w[:-1]
            tokens.append(w)
    return tokens

def _format_tokens(tokens):
    c = Counter(tokens)
    parts = []
    for word in sorted(c):
        if c[word] == 1:
            parts.append(word)
        else:
            parts.append(f"{c[word]}X {word}S")
    return " + ".join(parts)

def _remove_one(tokens, kind):
    k = kind.upper()
    if k.endswith("S"): k = k[:-1]
    try:
        tokens.remove(k)
    except ValueError:
        pass
    return tokens

def run(booking_id: str, kind: str, start_iso: str, end_iso: str):
    start = dtp.isoparse(start_iso)
    end   = dtp.isoparse(end_iso)

    # 1) Delete Disco buffer(s) for this Peerspace booking
    booking_key = f"ps|{booking_id}|{start.date()}"
    deleted = delete_events_by_private(get_cal_id(CAL_DISCO), "booking_key", booking_key)
    print(f"[Disco] Buffers deleted: {deleted}")

    # 2) Revert Airbnb block titles for each affected date
    for d in sorted(block_dates_for_event(start, end)):
        ev = find_all_day_event_on_date(get_cal_id(CAL_BLOCK), d)
        if not ev:
            print(f"[Block] No block found to adjust on {d}")
            continue

        tokens = _normalize_tokens(ev.get("summary",""))
        tokens = _remove_one(tokens, "PHOTOSHOOT" if kind.upper()=="PHOTOSHOOT" else "EVENT")

        if not tokens:
            # If nothing remains, delete the block entirely
            from tools.gcal_tool import _svc
            s=_svc()
            s.events().delete(calendarId=get_cal_id(CAL_BLOCK), eventId=ev["id"]).execute()
            print(f"[Block] Deleted empty block on {d}")
        else:
            new_summary = _format_tokens(tokens)
            update_event_summary(get_cal_id(CAL_BLOCK), ev["id"], new_summary)
            print(f"[Block] Updated {d}: {ev.get('summary')} → {new_summary}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python3 -m actions.peerspace_cancel <BOOKING_ID> <EVENT|PHOTOSHOOT> <START_ISO> <END_ISO>")
        sys.exit(1)
    run(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])