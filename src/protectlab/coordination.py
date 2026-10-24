import numpy as np


def audit(currents_a, pickups_a, multipliers, pairs, curve="very", grading_s=0.2, breaker_s=0.04):
    from .core import finite, positive
    from .overcurrent import operating_time

    current = finite(currents_a, real=True, ndim=2)
    pickup = finite(pickups_a, real=True, ndim=1)
    multiplier = finite(multipliers, real=True, ndim=1)
    if (
        current.shape[1] != len(pickup)
        or multiplier.shape != pickup.shape
        or np.any(pickup <= 0)
        or np.any(multiplier <= 0)
    ):
        raise ValueError("aligned positive relay pickups and multipliers required")
    grading = positive(grading_s, allow_zero=True)
    clearing = positive(breaker_s, allow_zero=True)
    times = operating_time(current / pickup, curve) * multiplier
    rows = []
    for fault, primary, backup in pairs:
        if (
            not 0 <= fault < len(current)
            or not 0 <= primary < len(pickup)
            or not 0 <= backup < len(pickup)
            or primary == backup
        ):
            raise ValueError("valid distinct primary-backup indices required")
        observable = np.isfinite(times[fault, primary]) and np.isfinite(times[fault, backup])
        margin = float(times[fault, backup] - times[fault, primary] - clearing) if observable else None
        rows.append(
            {
                "fault": fault,
                "primary": primary,
                "backup": backup,
                "observable": bool(observable),
                "margin_s": margin,
                "coordinated": bool(observable and margin >= grading - 1e-10),
            }
        )
    return {"times_s": times, "rows": rows, "coordinated": all(row["coordinated"] for row in rows)}
