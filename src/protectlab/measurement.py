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
