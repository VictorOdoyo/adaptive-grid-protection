import numpy as np
import pytest

from protectlab import overcurrent as m


def test_inverse_curves_match_published_scalar_anchor_and_pickup_limit():
    assert m.operating_time(2, "very", 0.1) == pytest.approx(1.35)
    assert np.isinf(m.operating_time(1))
    assert m.operating_time(10, "extreme", 0.2) == pytest.approx(16 / 99)
