import numpy as np
import pytest

from protectlab import instrument as m


def test_ct_excitation_is_continuous_odd_and_steeper_past_knee():
    ct = m.CT()
    at = m.excitation(np.array([-0.15, 0, 0.15, 0.16]), ct)
    assert at[0] == pytest.approx(-at[2])
    assert at[3] - at[2] == pytest.approx(0.01 / ct.saturated_h)
