import hashlib
import json

FIELDS = ["source", "external_id", "space", "kind", "start", "end"]

def event_hash(payload: dict) -> str:
    canon = {k: payload[k] for k in FIELDS}
    s = json.dumps(canon, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode()).hexdigest()[:16]
