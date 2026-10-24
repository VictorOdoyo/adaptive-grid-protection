from dataclasses import dataclass

import numpy as np


def priority_current(active, reactive, limit, priority="reactive"):
    from .core import positive

    limit = positive(limit)
    if not np.all(np.isfinite([active, reactive])) or priority not in ("reactive", "active"):
        raise ValueError("finite requests and active or reactive priority required")
    first, second = (reactive, active) if priority == "reactive" else (active, reactive)
    first = float(np.clip(first, -limit, limit))
    second = float(
        np.clip(second, -np.sqrt(max(0, limit**2 - first**2)), np.sqrt(max(0, limit**2 - first**2)))
    )
    return complex(second, -first) if priority == "reactive" else complex(first, -second)


def phase_limit(positive_current, negative_current, phase_limit_a):
    from .core import abc, finite, positive

    requested = abc([0, positive_current, negative_current])
    finite(requested)
    ceiling = positive(phase_limit_a)
    scale = min(1.0, ceiling / max(float(np.max(abs(requested))), 1e-30))
    return requested * scale


@dataclass(frozen=True)
class Inverter:
    name: str
    bus: str
    rated_current_a: float
    nominal_phase_v: float
    active_current_pu: float = 0.8
    reactive_current_pu: float = 0.0
    limit_pu: float = 1.2
    support_gain: float = 2.0
    negative_gain: float = 0.0
    priority: str = "reactive"

    def __post_init__(self):
        from .core import positive

        for field in ("rated_current_a", "nominal_phase_v", "limit_pu"):
            positive(getattr(self, field), field)
        for field in ("support_gain", "negative_gain"):
            positive(getattr(self, field), field, allow_zero=True)
        if not np.all(np.isfinite([self.active_current_pu, self.reactive_current_pu])):
            raise ValueError("finite current setpoints required")
        if self.priority not in ("active", "reactive"):
            raise ValueError("unknown priority")


def requested_current(model, voltage):
    from .core import seq

    _, v1, v2 = seq(voltage)
    angle = np.angle(v1) if abs(v1) > model.nominal_phase_v * 1e-6 else 0.0
    iq = model.reactive_current_pu + model.support_gain * max(0.0, 1 - abs(v1) / model.nominal_phase_v)
    positive = priority_current(model.active_current_pu, iq, model.limit_pu, model.priority) * np.exp(
        1j * angle
    )
    negative = -model.negative_gain * v2 / model.nominal_phase_v
    return phase_limit(
        positive * model.rated_current_a,
        negative * model.rated_current_a,
        model.limit_pu * model.rated_current_a,
    )


def solve_network(buses, branches, sources, inverters, shunts=None, fault=None):
    from scipy.optimize import root

    from .network import solve

    buses = tuple(buses)
    names = [i.name for i in inverters]
    if len(set(names)) != len(names) or any(i.bus not in buses for i in inverters):
        raise ValueError("unique inverter names at known buses required")
    if not inverters:
        result = solve(buses, branches, sources, shunts, fault=fault)
        return {**result, "inverter_current": {}, "control_residual": 0.0}
    size = 3 * len(inverters)
    scale = max(i.rated_current_a for i in inverters)

    def evaluate(vector, ret=False):
        complex_current = (vector[:size] + 1j * vector[size:]).reshape(-1, 3) * scale
        injections = {}
        for model, current in zip(inverters, complex_current, strict=True):
            injections[model.bus] = injections.get(model.bus, np.zeros(3, complex)) + current
        solved = solve(buses, branches, sources, shunts, injections, fault)
        target = np.array([requested_current(i, solved["voltage"][i.bus]) for i in inverters])
        difference = (complex_current - target).ravel() / scale
        return (solved, complex_current) if ret else np.r_[difference.real, difference.imag]

    guess = np.zeros(2 * size)
    fit = root(evaluate, guess, tol=1e-10)
    residual = float(np.max(abs(evaluate(fit.x))))
    if residual > 1e-7:
        raise RuntimeError("inverter/network control equilibrium did not converge")
    result, current = evaluate(fit.x, True)
    return {
        **result,
        "inverter_current": {i.name: c for i, c in zip(inverters, current, strict=True)},
        "control_residual": residual,
    }


def response(time, target, time_constant_s, initial=None):
    from .core import finite, positive, timebase

    t = timebase(time)
    target = finite(target)
    tau = positive(time_constant_s)
    if target.shape[0] != len(t):
        raise ValueError("aligned target current trajectory required")
    current = np.empty_like(target)
    current[0] = target[0] if initial is None else initial
    for k in range(1, len(t)):
        decay = np.exp(-(t[k] - t[k - 1]) / tau)
        current[k] = decay * current[k - 1] + (1 - decay) * target[k - 1]
    return current
