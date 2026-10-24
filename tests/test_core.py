import numpy as np
import pytest

from protectlab import core as m


def test_finite_rejects_nan_and_complex_measurements():
    with pytest.raises(ValueError):
        m.finite([np.nan])
    with pytest.raises(ValueError):
        m.finite([1j], real=True)
