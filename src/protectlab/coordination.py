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


def optimize(
    currents_a,
    pickups_a,
    pairs,
    curve="very",
    grading_s=0.2,
    breaker_s=0.04,
    bounds=(0.02, 2.0),
    weights=None,
):
    from scipy.optimize import linprog

    from .core import finite, positive
    from .overcurrent import operating_time

    current = finite(currents_a, real=True, ndim=2)
    pickup = finite(pickups_a, real=True, ndim=1)
    if current.shape[1] != len(pickup) or np.any(pickup <= 0):
        raise ValueError("aligned positive pickups required")
    unit = operating_time(current / pickup, curve)
    lower, upper = bounds
    if not 0 < lower <= upper or not np.all(np.isfinite(bounds)):
        raise ValueError("positive ordered finite multiplier bounds required")
    objective = np.ones(len(pickup)) if weights is None else finite(weights, real=True, ndim=1)
    if objective.shape != pickup.shape or np.any(objective <= 0):
        raise ValueError("positive objective weights required")
    matrix = []
    rhs = []
    margin = positive(grading_s, allow_zero=True) + positive(breaker_s, allow_zero=True)
    for fault, primary, backup in pairs:
        if (
            not (0 <= fault < len(current) and 0 <= primary < len(pickup) and 0 <= backup < len(pickup))
            or primary == backup
        ):
            raise ValueError("valid coordination indices required")
        if not np.isfinite(unit[fault, primary]) or not np.isfinite(unit[fault, backup]):
            raise ValueError("unobservable relay cannot be coordinated by time multiplier")
        row = np.zeros(len(pickup))
        row[primary], row[backup] = unit[fault, primary], -unit[fault, backup]
        matrix.append(row)
        rhs.append(-margin)
    fit = linprog(
        objective,
        A_ub=np.array(matrix) if matrix else None,
        b_ub=np.array(rhs) if rhs else None,
        bounds=[bounds] * len(pickup),
        method="highs",
    )
    if not fit.success:
        raise ValueError("coordination problem is infeasible: " + fit.message)
    certificate = audit(current, pickup, fit.x, pairs, curve, grading_s, breaker_s)
    if not certificate["coordinated"]:
        raise RuntimeError("optimized settings failed independent margin audit")
    return {"multipliers": fit.x, "objective": float(objective @ fit.x), "audit": certificate}


def pickup_interval(maximum_load_a, minimum_fault_a, load_margin=1.25, sensitivity=1.5):
    from .core import positive

    lower = positive(maximum_load_a) * positive(load_margin)
    upper = positive(minimum_fault_a) / positive(sensitivity)
    return {"minimum_pickup_a": lower, "maximum_pickup_a": upper, "feasible": bool(lower < upper)}
