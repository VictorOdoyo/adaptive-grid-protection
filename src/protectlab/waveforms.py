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


def envelope(time, initial, events):
    from .core import finite, timebase

    t = timebase(time)
    initial = finite(initial)
    if initial.shape != (3,):
        raise ValueError("three-phase initial phasors required")
    values = np.broadcast_to(initial, (len(t), 3)).copy()
    previous = -np.inf
    for when, phasor in events:
        if not np.isfinite(when) or when <= previous:
            raise ValueError("strictly ordered finite events required")
        phasor = finite(phasor)
        if phasor.shape != (3,):
            raise ValueError("three-phase event values required")
        values[t >= when] = phasor
        previous = when
    return values


def dc_offset(time, before, after, inception_s, tau_s, frequency_hz=50):
    from .core import finite, positive, timebase

    t = timebase(time)
    before, after = finite(before), finite(after)
    if before.shape != (3,) or after.shape != (3,):
        raise ValueError("three pre/post fault phasors required")
    tau = positive(tau_s)
    offset = np.zeros((len(t), 3))
    mismatch = np.sqrt(2) * np.real(
        (before - after) * np.exp(2j * np.pi * positive(frequency_hz) * inception_s)
    )
    selected = t >= inception_s
    offset[selected] = np.exp(-(t[selected] - inception_s) / tau)[:, None] * mismatch
    return offset
