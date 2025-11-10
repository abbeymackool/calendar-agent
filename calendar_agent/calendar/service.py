from calendar_agent.models.booking import Booking
from calendar_agent.calendar.mapping import booking_to_event
from calendar_agent.store.hashing import event_hash

class _Repo:
    _by_key = {}
    def find(self, s, x, c): return self._by_key.get((s,x,c))
    def insert(self, s, x, c, h, pid): self._by_key[(s,x,c)]={"hash":h,"provider_id":pid}
    def update(self, s, x, c, h): self._by_key[(s,x,c)]["hash"]=h

def upsert_booking(b: Booking, create_fn, update_fn) -> str:
    ev = booking_to_event(b)
    h = event_hash({
        "source": b.source, "external_id": b.external_id, "space": b.space,
        "kind": b.kind, "start": b.start.isoformat(), "end": b.end.isoformat()
    })
    ev.uid = f"{b.source}:{b.external_id}:{h}"
    repo = _Repo()
    existing = repo.find(b.source, b.external_id, ev.calendar_id)
    if not existing:
        provider_id = create_fn(ev)
        repo.insert(b.source, b.external_id, ev.calendar_id, h, provider_id)
        return provider_id
    if existing["hash"] != h:
        update_fn(existing["provider_id"], ev)
        repo.update(b.source, b.external_id, ev.calendar_id, h)
    return existing["provider_id"]

def cancel_by_source_id(source: str, external_id: str, space: str, delete_fn) -> None:
    pass
