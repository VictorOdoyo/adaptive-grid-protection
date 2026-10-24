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
