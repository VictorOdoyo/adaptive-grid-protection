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


def mho(impedance, reach_ohm, valid=True, forward=True):
    from .core import finite

    z = finite(impedance)
    reach = complex(finite(reach_ohm))
    if abs(reach) == 0:
        raise ValueError("nonzero mho reach required")
    return (
        np.asarray(valid, bool)
        & np.asarray(forward, bool)
        & (abs(z - reach / 2) <= abs(reach) / 2 * (1 + 1e-12))
    )


def polygon(impedance, vertices, valid=True):
    from .core import finite

    z = finite(impedance)
    points = finite(vertices, ndim=1)
    if len(points) < 3:
        raise ValueError("at least three polygon vertices required")
    edge = np.roll(points, -1) - points
    turn = np.imag(np.conj(edge) * np.roll(edge, -1))
    if np.any(abs(edge) < 1e-12) or not (np.all(turn > 0) or np.all(turn < 0)):
        raise ValueError("strictly convex ordered polygon required")
    cross = np.imag(np.conj(edge) * (z[..., None] - points))
    tolerance = 1e-12 * max(1, float(np.max(abs(points))) ** 2)
    inside = np.all(cross >= -tolerance, axis=-1) | np.all(cross <= tolerance, axis=-1)
    return np.asarray(valid, bool) & inside


def load_encroachment(impedance, minimum_ohm, half_angle_rad=np.pi / 6):
    from .core import finite, positive

    z = finite(impedance)
    if not 0 < half_angle_rad < np.pi / 2:
        raise ValueError("load wedge half angle in (0,pi/2) required")
    angle = abs(np.angle(z))
    near_real = np.minimum(angle, abs(np.pi - angle)) < half_angle_rad
    return (abs(z) >= positive(minimum_ohm)) & near_real
