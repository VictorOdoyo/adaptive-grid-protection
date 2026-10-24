from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CT:
    ratio: float = 200.0
    burden_ohm: float = 1.0
    magnetizing_h: float = 20.0
    saturated_h: float = 0.02
    knee_vs: float = 0.15

    def __post_init__(self):
        from .core import positive

        for name in ("ratio", "burden_ohm", "magnetizing_h", "saturated_h", "knee_vs"):
            positive(getattr(self, name), name)
        if self.saturated_h > self.magnetizing_h:
            raise ValueError("saturated inductance cannot exceed unsaturated inductance")


def excitation(flux_vs, model):
    from .core import finite

    phi = finite(flux_vs, real=True)
    magnitude = abs(phi)
    return np.sign(phi) * (
        np.minimum(magnitude, model.knee_vs) / model.magnetizing_h
        + np.maximum(0, magnitude - model.knee_vs) / model.saturated_h
    )


def simulate(time, primary_a, model=None, initial_flux_vs=0.0):
    from .core import finite, timebase

    t = timebase(time)
    primary = finite(primary_a, real=True, ndim=1)
    model = CT() if model is None else model
    if primary.shape != t.shape or not np.isfinite(initial_flux_vs):
        raise ValueError("aligned real primary samples and finite initial flux required")
    flux = np.empty(len(t))
    flux[0] = initial_flux_vs
    for k, dt in enumerate(np.diff(t), 1):
        h = dt * model.burden_ohm
        rhs = flux[k - 1] + h * primary[k] / model.ratio
        linear = rhs / (1 + h / model.magnetizing_h)
        if abs(linear) <= model.knee_vs:
            flux[k] = linear
        else:
            flux[k] = (
                np.sign(rhs)
                * (abs(rhs) + h * model.knee_vs * (1 / model.saturated_h - 1 / model.magnetizing_h))
                / (1 + h / model.saturated_h)
            )
    magnetizing = excitation(flux, model)
    secondary = primary / model.ratio - magnetizing
    return {
        "secondary_a": secondary,
        "flux_vs": flux,
        "magnetizing_a": magnetizing,
        "saturated": abs(flux) > model.knee_vs,
    }


def magnetic_energy(flux_vs, model):
    from .core import finite

    magnitude = abs(finite(flux_vs, real=True))
    inner = np.minimum(magnitude, model.knee_vs)
    outer = np.maximum(0, magnitude - model.knee_vs)
    return (
        0.5 * inner**2 / model.magnetizing_h
        + model.knee_vs / model.magnetizing_h * outer
        + 0.5 * outer**2 / model.saturated_h
    )


def energy_audit(time, primary_a, capture, model):
    from .core import integrate

    secondary = capture["secondary_a"]
    voltage = model.burden_ohm * secondary
    input_energy = float(integrate(time, voltage * np.asarray(primary_a) / model.ratio).real)
    burden_energy = float(integrate(time, model.burden_ohm * secondary**2).real)
    stored = magnetic_energy(capture["flux_vs"], model)
    return {
        "input_j": input_energy,
        "burden_j": burden_energy,
        "storage_change_j": float(stored[-1] - stored[0]),
        "numerical_defect_j": input_energy - burden_energy - float(stored[-1] - stored[0]),
    }


def calibrate(secondary, ratio, angle_error_rad=0.0, polarity=1):
    from .core import finite, positive

    if polarity not in (-1, 1) or not np.isfinite(angle_error_rad):
        raise ValueError("signed polarity and finite phase calibration required")
    return finite(secondary) * positive(ratio) * polarity * np.exp(-1j * angle_error_rad)


def linear_response(frequency_hz, model):
    from .core import finite

    f = finite(frequency_hz, real=True)
    if np.any(f <= 0):
        raise ValueError("positive frequencies required")
    impedance = 2j * np.pi * f * model.magnetizing_h
    return impedance / (model.burden_ohm + impedance)
