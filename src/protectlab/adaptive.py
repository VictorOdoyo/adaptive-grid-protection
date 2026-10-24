def topology_hash(buses, branches, sources):
    import hashlib
    import json

    description = {
        "buses": sorted(buses),
        "branches": sorted(
            [{"name": b.name, "start": b.start, "end": b.end, "closed": bool(b.closed)} for b in branches],
            key=lambda x: x["name"],
        ),
        "sources": sorted([{"name": s.name, "bus": s.bus} for s in sources], key=lambda x: x["name"]),
    }
    return hashlib.sha256(json.dumps(description, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
