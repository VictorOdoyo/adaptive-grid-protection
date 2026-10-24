import numpy as np


def adc(values, full_scale, bits=16):
    from .core import finite, integer, positive

    v = finite(values, real=True)
    rail = positive(full_scale)
    integer(bits)
    if not 2 <= bits <= 24:
        raise ValueError("ADC resolution must be 2 to 24 bits")
    step = 2 * rail / (2**bits - 1)
    clipped = abs(v) > rail
    codes = np.rint((np.clip(v, -rail, rail) + rail) / step)
    return {"values": codes * step - rail, "clipped": clipped, "step": step}


def lowpass(values, sample_hz, cutoff_hz, order=4):
    from scipy.signal import butter, sosfilt

    from .core import finite, integer, positive

    values = finite(values, real=True)
    fs, fc = positive(sample_hz), positive(cutoff_hz)
    integer(order)
    if not fc < fs / 2:
        raise ValueError("cutoff must lie below Nyquist")
    return sosfilt(butter(order, fc, fs=fs, output="sos"), values, axis=0)


def decimate(values, sample_hz, factor, cutoff_hz=None):
    from .core import integer, positive

    integer(factor, 2)
    new_fs = positive(sample_hz) / factor
    cutoff = 0.4 * new_fs if cutoff_hz is None else positive(cutoff_hz)
    if cutoff >= new_fs / 2:
        raise ValueError("anti-alias cutoff exceeds new Nyquist")
    return {"values": lowpass(values, sample_hz, cutoff)[::factor], "sample_hz": new_fs}


def dft(time, values, frequency_hz=50, samples_per_cycle=None, quality=None):
    from .core import finite, integer, positive, timebase

    t = timebase(time)
    v = finite(values, real=True)
    if v.shape[0] != len(t):
        raise ValueError("aligned measurement samples required")
    dt = float(np.mean(np.diff(t)))
    if not np.allclose(np.diff(t), dt, rtol=1e-8, atol=dt * 1e-10):
        raise ValueError("DFT requires uniformly spaced samples")
    frequency = positive(frequency_hz)
    count = round(1 / (frequency * dt)) if samples_per_cycle is None else integer(samples_per_cycle, 2)
    if abs(count * frequency * dt - 1) > 1e-8 or count > len(t):
        raise ValueError("one integer nominal cycle and sufficient samples required")
    shape = (len(t),) + (1,) * (v.ndim - 1)
    demodulated = v * np.exp(-2j * np.pi * frequency * t).reshape(shape)
    cumulative = np.concatenate([np.zeros((1, *v.shape[1:]), complex), np.cumsum(demodulated, axis=0)])
    phasor = np.zeros(v.shape, complex)
    phasor[count - 1 :] = np.sqrt(2) / count * (cumulative[count:] - cumulative[:-count])
    valid = np.zeros(len(t), bool)
    valid[count - 1 :] = True
    if quality is not None:
        q = np.asarray(quality)
        if q.shape != t.shape or q.dtype != bool:
            raise ValueError("aligned boolean measurement quality required")
        bad = np.r_[0, np.cumsum(~q)]
        valid[count - 1 :] &= (bad[count:] - bad[:-count]) == 0
    return {"phasor": phasor, "valid": valid, "window_samples": count, "time_s": t.copy()}
