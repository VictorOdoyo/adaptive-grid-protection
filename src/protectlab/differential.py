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
