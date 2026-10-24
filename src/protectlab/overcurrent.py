import numpy as np

CURVES = {
    "standard": (0.14, 0.02, 0.0),
    "very": (13.5, 1.0, 0.0),
    "extreme": (80.0, 2.0, 0.0),
    "ieee-moderate": (0.0515, 0.02, 0.114),
    "ieee-very": (19.61, 2.0, 0.491),
    "ieee-extreme": (28.2, 2.0, 0.1217),
}


def operating_time(multiple, curve="standard", time_multiplier=1.0, minimum_s=0.0):
    from .core import finite, positive

    value = finite(multiple, real=True)
    if curve not in CURVES or np.any(value < 0):
        raise ValueError("known curve and nonnegative current multiple required")
    scale = positive(time_multiplier)
    minimum = positive(minimum_s, allow_zero=True)
    k, alpha, constant = CURVES[curve]
    active = value > 1
    result = np.full(value.shape, np.inf)
    result[active] = np.maximum(minimum, scale * (k / np.expm1(alpha * np.log(value[active])) + constant))
    return result
