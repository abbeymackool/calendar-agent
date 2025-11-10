import hashlib, json
FIELDS = ["source","external_id","space","kind","start","end"]
def event_hash(payload: dict) -> str:
    s = json.dumps({k: payload[k] for k in FIELDS}, sort_keys=True, separators=(",",":"))
    return hashlib.sha256(s.encode()).hexdigest()[:16]
PY]

cat > calendar_agent/store/hashing.py << 'PY'
import hashlib, json
FIELDS = ["source","external_id","space","kind","start","end"]
def event_hash(payload: dict) -> str:
    s = json.dumps({k: payload[k] for k in FIELDS}, sort_keys=True, separators=(",",":"))
    return hashlib.sha256(s.encode()).hexdigest()[:16]
