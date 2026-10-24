import numpy as np

from protectlab import frontend as m


def test_causal_frontend_reaches_correct_fundamental_magnitude():
    from protectlab.waveforms import synthesize

    t = np.arange(1000) / 3200
    wave = synthesize(t, [100 + 0j, 100 + 0j, 100 + 0j])
    front = m.Frontend()
    last = None
    for ti, values in zip(t, wave, strict=True):
        last = front.update(ti, values)
    assert np.allclose(abs(last), 100, rtol=1e-4)
