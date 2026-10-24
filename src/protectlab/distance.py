import numpy as np


def phase_loops(voltage, current, minimum_a=1e-3):
    from .core import finite, positive

    v, i = finite(voltage), finite(current)
    if v.shape != i.shape or v.shape[-1] != 3:
        raise ValueError("matching three-phase terminal arrays required")
    indices = [(0, 1), (1, 2), (2, 0)]
    numerator = np.stack([v[..., a] - v[..., b] for a, b in indices], axis=-1)
    denominator = np.stack([i[..., a] - i[..., b] for a, b in indices], axis=-1)
    valid = abs(denominator) >= positive(minimum_a)
    z = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=valid)
    return {"impedance_ohm": z, "valid": valid, "loops": ["ab", "bc", "ca"]}


def ground_loops(voltage, current, z0_ohm, z1_ohm, minimum_a=1e-3):
    from .core import finite, positive

    v, i = finite(voltage), finite(current)
    if v.shape != i.shape or v.shape[-1] != 3 or abs(z1_ohm) == 0:
        raise ValueError("matching phases and nonzero positive-sequence line impedance required")
    compensation = (z0_ohm - z1_ohm) / (3 * z1_ohm)
    denominator = i + compensation * np.sum(i, axis=-1, keepdims=True)
    valid = abs(denominator) >= positive(minimum_a)
    z = np.divide(v, denominator, out=np.zeros_like(v), where=valid)
    return {"impedance_ohm": z, "valid": valid, "k0": compensation}
