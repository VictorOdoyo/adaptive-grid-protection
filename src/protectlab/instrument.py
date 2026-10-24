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
