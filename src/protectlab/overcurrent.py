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


class InverseRelay:
    def __init__(self, pickup_a, curve="standard", time_multiplier=0.1, reset_s=0.1, dropout=0.95):
        from .core import positive

        self.pickup = positive(pickup_a)
        if curve not in CURVES or not 0 < dropout <= 1:
            raise ValueError("known curve and dropout fraction in (0,1] required")
        self.curve = curve
        self.multiplier = positive(time_multiplier)
        self.reset_s = positive(reset_s)
        self.dropout = dropout
        self.travel = 0.0
        self.picked = False
        self.tripped = False

    def update(self, current_a, dt_s, valid=True, blocked=False):
        from .core import positive

        current = positive(current_a, allow_zero=True)
        dt = positive(dt_s)
        if self.tripped:
            return True
        if not valid or blocked:
            self.travel = 0.0
            self.picked = False
            return False
        multiple = current / self.pickup
        self.picked = multiple > 1 if not self.picked else multiple > self.dropout
        if multiple > 1:
            self.travel += dt / float(operating_time(multiple, self.curve, self.multiplier))
        else:
            self.travel = max(0.0, self.travel - dt / self.reset_s)
        self.tripped = self.travel >= 1 - 1e-12
        return self.tripped


class DefiniteRelay:
    def __init__(self, pickup_a, delay_s=0.02, dropout=0.95):
        from .core import positive

        self.pickup = positive(pickup_a)
        self.delay = positive(delay_s, allow_zero=True)
        if not 0 < dropout <= 1:
            raise ValueError("dropout fraction in (0,1] required")
        self.dropout = dropout
        self.elapsed = 0.0
        self.picked = False
        self.tripped = False

    def update(self, current_a, dt_s, valid=True, blocked=False):
        from .core import positive

        current = positive(current_a, allow_zero=True)
        dt = positive(dt_s)
        if self.tripped:
            return True
        if not valid or blocked:
            self.elapsed = 0.0
            self.picked = False
            return False
        self.picked = current > self.pickup if not self.picked else current > self.pickup * self.dropout
        self.elapsed = self.elapsed + dt if self.picked else 0.0
        self.tripped = self.picked and self.elapsed >= self.delay - 1e-12
        return self.tripped


def phase_and_ground(current_phasors, phase_pickup_a, ground_pickup_a):
    from .core import finite, positive

    current = finite(current_phasors)
    if current.shape[-1] != 3:
        raise ValueError("three-phase currents required")
    phase = np.max(abs(current), axis=-1)
    ground = abs(np.sum(current, axis=-1))
    return {
        "phase_a": phase,
        "residual_a": ground,
        "phase_pickup": phase > positive(phase_pickup_a),
        "ground_pickup": ground > positive(ground_pickup_a),
    }


def voltage_restrained_pickup(voltage_pu, nominal_pickup_a, minimum_fraction=0.25):
    from .core import finite, positive

    voltage = finite(voltage_pu, real=True)
    if np.any(voltage < 0) or not 0 < minimum_fraction <= 1:
        raise ValueError("nonnegative voltage and restraint floor in (0,1] required")
    return positive(nominal_pickup_a) * np.clip(voltage, minimum_fraction, 1.0)
