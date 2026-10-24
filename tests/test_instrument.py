import numpy as np
import pytest

from protectlab import instrument as m


def test_ct_excitation_is_continuous_odd_and_steeper_past_knee():
    ct = m.CT()
    at = m.excitation(np.array([-0.15, 0, 0.15, 0.16]), ct)
    assert at[0] == pytest.approx(-at[2])
    assert at[3] - at[2] == pytest.approx(0.01 / ct.saturated_h)


def test_ct_linear_limit_matches_constant_primary_exponential():
    ct = m.CT(knee_vs=1000, magnetizing_h=1, burden_ohm=2)
    t = np.linspace(0, 1, 10001)
    r = m.simulate(t, np.ones(len(t)) * 200, ct)
    assert np.max(abs(r["secondary_a"] - np.exp(-2 * t))) < 4e-5
    assert not np.any(r["saturated"])


def test_ct_energy_gradient_matches_excitation_and_refinement_reduces_defect():
    ct = m.CT(knee_vs=0.02)
    phi = np.linspace(0.021, 0.08, 101)
    step = 1e-7
    derivative = (m.magnetic_energy(phi + step, ct) - m.magnetic_energy(phi - step, ct)) / (2 * step)
    assert np.allclose(derivative, m.excitation(phi, ct), rtol=1e-8)
    defects = []
    for n in (1001, 2001):
        t = np.linspace(0, 0.1, n)
        primary = 2000 * np.sin(2 * np.pi * 50 * t)
        cap = m.simulate(t, primary, ct)
        defects.append(abs(m.energy_audit(t, primary, cap, ct)["numerical_defect_j"]))
    assert defects[1] < defects[0] * 0.6


def test_instrument_calibration_reverses_declared_ratio_and_angle_error():
    expected = np.array([100 + 20j, 30 - 10j])
    measured = expected / 200 * np.exp(0.03j) * -1
    assert np.allclose(m.calibrate(measured, 200, 0.03, -1), expected)


def test_ct_frequency_response_has_physical_low_frequency_rolloff():
    ct = m.CT()
    h = m.linear_response([0.001, 50], ct)
    assert abs(h[0]) < 0.2
    assert abs(h[1]) > 0.999
    assert h[0].imag > 0
