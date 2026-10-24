import numpy as np


def quantities(left, right):
    from .core import finite

    left, right = np.broadcast_arrays(finite(left), finite(right))
    return {"operate_a": abs(left + right), "restraint_a": 0.5 * (abs(left) + abs(right))}


def characteristic(left, right, pickup_a=10, slope_low=0.2, slope_high=0.6, breakpoint_a=200):
    from .core import positive

    pickup = positive(pickup_a)
    low = positive(slope_low, allow_zero=True)
    high = positive(slope_high, allow_zero=True)
    point = positive(breakpoint_a)
    if high < low:
        raise ValueError("high restraint slope must be at least low slope")
    q = quantities(left, right)
    restraint = q["restraint_a"]
    threshold = pickup + low * np.minimum(restraint, point) + high * np.maximum(restraint - point, 0)
    return {**q, "threshold_a": threshold, "pickup": q["operate_a"] > threshold}


def harmonic_block(fundamental, second, threshold=0.15, cross_phase=False, minimum_a=1):
    from .core import finite, positive

    f, s = np.broadcast_arrays(abs(finite(fundamental)), abs(finite(second)))
    valid = f >= positive(minimum_a)
    ratio = np.divide(s, f, out=np.zeros_like(f), where=valid)
    blocked = valid & (ratio >= positive(threshold))
    if cross_phase:
        if blocked.shape[-1] != 3:
            raise ValueError("three-phase harmonic channels required for cross blocking")
        blocked = np.broadcast_to(np.any(blocked, axis=-1, keepdims=True), blocked.shape).copy()
    return {"ratio": ratio, "valid": valid, "blocked": blocked}


def compensate(current, ratio=1.0, clock=0, remove_zero_sequence=False):
    from .core import finite, integer, positive

    i = finite(current)
    if i.shape[-1] != 3:
        raise ValueError("three phase winding currents required")
    integer(clock, 0)
    if clock > 11:
        raise ValueError("transformer clock must be 0 to 11")
    if remove_zero_sequence:
        i = i - np.mean(i, axis=-1, keepdims=True)
    return i * positive(ratio) * np.exp(-1j * clock * np.pi / 6)


def supervised(
    left,
    right,
    left_time_s,
    right_time_s,
    now_s,
    maximum_skew_s=0.001,
    maximum_age_s=0.02,
    valid=True,
    blocked=False,
    **settings,
):
    from .core import positive

    skew = positive(maximum_skew_s)
    age = positive(maximum_age_s)
    times = np.array([left_time_s, right_time_s, now_s])
    usable = bool(valid) and np.all(np.isfinite(times)) and abs(left_time_s - right_time_s) <= skew
    usable = usable and min(now_s - left_time_s, now_s - right_time_s) >= 0
    usable = usable and max(now_s - left_time_s, now_s - right_time_s) <= age
    result = characteristic(left, right, **settings)
    return {**result, "valid": usable, "trip": result["pickup"] & usable & ~np.asarray(blocked, bool)}
