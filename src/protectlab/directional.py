import numpy as np


def torque(voltage, current, maximum_torque_rad=0.0, minimum_voltage=1e-6, minimum_current=1e-6):
    from .core import finite, positive

    v, i = np.broadcast_arrays(finite(voltage), finite(current))
    if not np.isfinite(maximum_torque_rad):
        raise ValueError("finite maximum torque angle required")
    valid = (abs(v) >= positive(minimum_voltage)) & (abs(i) >= positive(minimum_current))
    value = np.real(v * np.conj(i) * np.exp(-1j * maximum_torque_rad))
    return {
        "torque_va": value,
        "valid": valid,
        "forward": valid & (value > 0),
        "reverse": valid & (value < 0),
    }
