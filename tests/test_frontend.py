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


def test_current_frontend_blocks_adc_clipped_fourier_windows():
    from protectlab.instrument import CT
    from protectlab.waveforms import synthesize

    front = m.CurrentFrontend(ct=CT(ratio=10, knee_vs=1000), full_scale_a=1)
    t = np.arange(200) / 3200
    output = [front.update(ti, value) for ti, value in zip(t, synthesize(t, [100, 100, 100]), strict=True)]
    assert output[-1] is None
    assert np.any(front.clipped)
