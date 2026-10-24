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


def certify(group, currents_a, pairs, grading_s=0.2, breaker_s=0.04):
    import hashlib
    import json

    from .coordination import audit
    from .core import finite

    currents = finite(currents_a, real=True, ndim=2)
    result = audit(currents, group.pickups_a, group.multipliers, pairs, group.curve, grading_s, breaker_s)
    if not result["coordinated"]:
        raise ValueError("setting group fails its modeled fault envelope")
    envelope = {
        "currents_a": currents.tolist(),
        "pairs": list(pairs),
        "grading_s": grading_s,
        "breaker_s": breaker_s,
    }
    seal = hashlib.sha256(json.dumps(envelope, sort_keys=True).encode()).hexdigest()
    return {
        "group_sha256": group.digest(),
        "envelope_sha256": seal,
        "envelope": envelope,
        "rows": result["rows"],
    }


def verify_certificate(group, certificate):
    try:
        envelope = certificate["envelope"]
        expected = certify(
            group, envelope["currents_a"], envelope["pairs"], envelope["grading_s"], envelope["breaker_s"]
        )
        return expected == certificate
    except (ValueError, KeyError, TypeError):
        return False


class Manager:
    def __init__(self, initial, certificate, maximum_age_s=0.1, commit_delay_s=0.02):
        from .core import positive

        if not verify_certificate(initial, certificate):
            raise ValueError("initial settings require a valid modeled-envelope certificate")
        self.active = initial
        self.maximum_age = positive(maximum_age_s)
        self.delay = positive(commit_delay_s, allow_zero=True)
        self.pending = None
        self.history = []

    def propose(self, group, certificate, topology, observed_s, now_s):
        if not np.all(np.isfinite([observed_s, now_s])) or not 0 <= now_s - observed_s <= self.maximum_age:
            raise ValueError("fresh nonfuture topology observation required")
        if group.topology != topology or group.revision <= self.active.revision:
            raise ValueError("matching topology and increasing setting revision required")
        if not verify_certificate(group, certificate):
            raise ValueError("setting certificate is invalid")
        self.pending = {"group": group, "topology": topology, "observed_s": observed_s, "proposed_s": now_s}
        self.history.append({"time_s": now_s, "event": "proposed", "group": group.name})


def commit(manager, now_s, topology, observed_s, fault_active=False):
    if not np.all(np.isfinite([now_s, observed_s])):
        raise ValueError("finite adaptive clock required")
    pending = manager.pending
    if pending is None:
        return False
    if topology != pending["topology"] or not 0 <= now_s - observed_s <= manager.maximum_age:
        manager.history.append({"time_s": now_s, "event": "cancelled", "group": pending["group"].name})
        manager.pending = None
        return False
    if fault_active or now_s - pending["proposed_s"] < manager.delay - 1e-12:
        return False
    manager.active = pending["group"]
    manager.pending = None
    manager.history.append({"time_s": now_s, "event": "committed", "group": manager.active.name})
    return True
