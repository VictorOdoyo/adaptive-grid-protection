import numpy as np
import pytest

from protectlab import measurement as m


def test_adc_reports_rails_and_half_lsb_error():
    v = np.array([-20, -2.1, 0, 3.2, 20])
    r = m.adc(v, 10, 12)
    assert np.array_equal(r["clipped"], [True, False, False, False, True])
    assert np.max(abs(r["values"][1:4] - v[1:4])) <= r["step"] / 2 + 1e-12


def test_analog_filter_attenuates_high_frequency_without_future_samples():
    fs = 10000
    t = np.arange(20000) / fs
    v = np.sin(2 * np.pi * 2000 * t)
    out = m.lowpass(v, fs, 300)
    assert np.std(out[10000:]) < 0.001
    impulse = np.zeros(100)
    impulse[50] = 1
    assert np.all(m.lowpass(impulse, fs, 300)[:50] == 0)


def test_decimation_tracks_physical_rate_and_rejects_aliasing_cutoff():
    result = m.decimate(np.ones(1000), 10000, 5)
    assert len(result["values"]) == 200 and result["sample_hz"] == 2000
    with pytest.raises(ValueError):
        m.decimate(np.ones(100), 10000, 5, 1500)
