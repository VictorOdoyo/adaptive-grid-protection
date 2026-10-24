import numpy as np


def synthesize(time, phasors, frequency_hz=50):
    from .core import finite, positive, timebase

    t = timebase(time)
    p = finite(phasors)
    if p.shape == (3,):
        p = np.broadcast_to(p, (len(t), 3))
    if p.shape != (len(t), 3):
        raise ValueError("three RMS phasors per timestamp required")
    return np.sqrt(2) * np.real(p * np.exp(2j * np.pi * positive(frequency_hz) * t[:, None]))
