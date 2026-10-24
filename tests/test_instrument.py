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
