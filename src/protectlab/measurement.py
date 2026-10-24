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
