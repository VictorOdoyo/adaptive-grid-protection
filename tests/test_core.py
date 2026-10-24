import numpy as np
import pytest

from protectlab import core as m


def test_finite_rejects_nan_and_complex_measurements():
    with pytest.raises(ValueError):
        m.finite([np.nan])
    with pytest.raises(ValueError):
        m.finite([1j], real=True)


@pytest.mark.parametrize("value", [True, -1, float("inf"), 1j])
def test_positive_scalar_contract(value):
    with pytest.raises(ValueError):
        m.positive(value)
    with pytest.raises(ValueError):
        m.integer(2.5)


def test_sequence_roundtrip_and_positive_phase_rotation():
    phases = m.abc([0, 100, 0])
    assert np.allclose(phases, [100, 100 * np.exp(-2j * np.pi / 3), 100 * np.exp(2j * np.pi / 3)])
    assert np.allclose(m.seq(phases), [0, 100, 0], atol=1e-12)
