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


class MemoryVoltage:
    def __init__(self, minimum_v, hold_s=0.1, time_constant_s=0.02):
        from .core import positive

        self.minimum = positive(minimum_v)
        self.hold = positive(hold_s)
        self.tau = positive(time_constant_s)
        self.memory = 0j
        self.age = np.inf

    def update(self, voltage, dt_s, valid=True):
        from .core import finite, positive

        v = complex(finite(voltage))
        dt = positive(dt_s)
        if valid and abs(v) >= self.minimum:
            if not np.isfinite(self.age):
                self.memory = v
            else:
                self.memory += (v - self.memory) * (-np.expm1(-dt / self.tau))
            self.age = 0.0
        else:
            self.age += dt
        usable = self.age <= self.hold and abs(self.memory) >= self.minimum
        return {"voltage": self.memory, "valid": usable, "age_s": self.age}
