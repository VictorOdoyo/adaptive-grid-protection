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


def test_dft_preserves_absolute_phase_and_propagates_one_bad_sample():
    from protectlab.waveforms import synthesize

    t = 0.013 + np.arange(400) / 10000
    expected = np.array([10 + 3j, 2 - 8j, 5j])
    q = np.ones(len(t), bool)
    q[205] = False
    result = m.dft(t, synthesize(t, expected), quality=q)
    assert np.allclose(result["phasor"][199:], expected, atol=1e-11)
    assert not np.any(result["valid"][205:])
    assert result["valid"][204]


def test_true_rms_includes_harmonic_energy():
    from protectlab.waveforms import harmonics

    t = np.arange(800) / 10000
    wave = harmonics(t, {1: [10, 10, 10], 3: [4, 4, 4]})
    result = m.sliding_rms(wave, 200)
    assert np.allclose(result["rms"][199:], np.sqrt(116))
    assert not result["valid"][0]


def test_joint_fit_recovers_off_nominal_harmonics_and_dc():
    from protectlab.waveforms import harmonics

    t = np.linspace(0.003, 0.039, 250)
    expected = np.array([10 + 2j, 8 - 3j, 4j])
    wave = harmonics(t, {1: expected, 2: expected * 0.2}, 49.3) + 3
    result = m.least_squares(t, wave, 49.3, orders=(1, 2))
    assert np.allclose(result["phasors"][1], expected)
    assert np.allclose(result["phasors"][2], expected * 0.2)
    assert np.allclose(result["dc"], 3)
    assert result["residual"] < 1e-12


def test_frequency_tracking_keeps_nominal_and_increment_separate():
    t = np.arange(1000) / 1000
    p = 10 * np.exp(2j * np.pi * (-0.7) * t)
    result = m.frequency(t, p)
    assert np.allclose(result["frequency_hz"][1:], 49.3)
    p[10] = 0
    assert not m.frequency(t, p)["valid"][10]


def test_mimic_cancels_matching_dc_exponential_and_exposes_phase_shift():
    t = np.arange(1000) / 10000
    result = m.mimic(np.exp(-t / 0.03), 10000, 0.03)
    assert np.max(abs(result["values"][1:])) < 1e-12
    assert abs(result["response"]) == pytest.approx(1)
    assert abs(np.angle(result["response"])) > 1
