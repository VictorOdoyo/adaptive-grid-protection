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


def test_phase_impedance_preserves_sequence_network():
    z = np.array([3 + 8j, 1 + 2j, 1 + 2j])
    current = np.array([2 + 1j, 4, 3j])
    assert np.allclose(m.seq(m.phase_matrix(z) @ m.abc(current)), z * current)


def test_rms_power_has_no_peak_phasor_half_factor():
    v = m.abc([0, 230, 0])
    i = m.abc([0, 10 - 2j, 0])
    assert m.power(v, i) == pytest.approx(6900 + 1380j)


def test_three_phase_bases_preserve_per_phase_ohms():
    b = m.bases(1e6, 11000)
    assert b["impedance_ohm"] == pytest.approx(b["phase_voltage_v"] / b["current_a"])


def test_named_streams_are_repeatable_and_distinct():
    assert np.array_equal(m.stream(42, "adc").normal(size=8), m.stream(42, "adc").normal(size=8))
    assert not np.array_equal(m.stream(42, "adc").normal(size=8), m.stream(42, "ct").normal(size=8))


def test_time_integrals_use_actual_nonuniform_spacing():
    assert m.integrate([0, 0.1, 0.4], [0, 0.1, 0.4]) == pytest.approx(0.08)
    with pytest.raises(ValueError):
        m.timebase([0, 0, 1])
