from dataclasses import dataclass

import numpy as np


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


@dataclass(frozen=True)
class Group:
    name: str
    topology: str
    revision: int
    pickups_a: tuple
    multipliers: tuple
    curve: str = "very"

    def __post_init__(self):
        from .core import finite, integer
        from .overcurrent import CURVES

        integer(self.revision)
        p, t = finite(self.pickups_a, real=True, ndim=1), finite(self.multipliers, real=True, ndim=1)
        if (
            not self.name
            or not self.topology
            or p.size == 0
            or p.shape != t.shape
            or np.any(p <= 0)
            or np.any(t <= 0)
        ):
            raise ValueError("named topology and matching positive relay settings required")
        if self.curve not in CURVES:
            raise ValueError("unknown inverse curve")
        object.__setattr__(self, "pickups_a", tuple(p))
        object.__setattr__(self, "multipliers", tuple(t))

    def to_dict(self):
        return {
            "name": self.name,
            "topology": self.topology,
            "revision": self.revision,
            "pickups_a": list(self.pickups_a),
            "multipliers": list(self.multipliers),
            "curve": self.curve,
        }

    def digest(self):
        import hashlib
        import json

        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
