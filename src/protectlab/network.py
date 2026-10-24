from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Branch:
    name: str
    start: str
    end: str
    z: object
    closed: bool = True

    def __post_init__(self):
        from .core import finite

        z = finite(self.z, ndim=2).copy()
        if z.shape != (3, 3) or np.linalg.matrix_rank(z) < 3 or not np.allclose(z, z.T):
            raise ValueError("reciprocal invertible 3x3 series impedance required")
        if np.linalg.eigvalsh(z.real).min() < -1e-12:
            raise ValueError("passive branch resistance required")
        if not self.name or not self.start or self.start == self.end:
            raise ValueError("named distinct branch endpoints required")
        z.setflags(write=False)
        object.__setattr__(self, "z", z)


@dataclass(frozen=True)
class Source:
    name: str
    bus: str
    emf: object
    z: object

    def __post_init__(self):
        from .core import finite

        emf = finite(self.emf).copy()
        checked = Branch(self.name, self.bus, self.bus + "__internal", self.z)
        if emf.shape != (3,):
            raise ValueError("three RMS source phase emfs required")
        emf.setflags(write=False)
        object.__setattr__(self, "emf", emf)
        object.__setattr__(self, "z", checked.z)


def balanced_source(name, bus, phase_voltage_v, z0, z1, z2=None, angle_rad=0):
    from .core import abc, phase_matrix, positive

    emf = abc([0, positive(phase_voltage_v) * np.exp(1j * angle_rad), 0])
    return Source(name, bus, emf, phase_matrix([z0, z1, z1 if z2 is None else z2]))
