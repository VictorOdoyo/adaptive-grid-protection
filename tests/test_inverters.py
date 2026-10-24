import pytest

from protectlab import inverters as m


def test_reactive_priority_preserves_var_request_under_current_ceiling():
    i = m.priority_current(10, 8, 10)
    assert i == pytest.approx(6 - 8j)
    assert abs(m.priority_current(10, 8, 10, "active")) == pytest.approx(10)


def test_sequence_sum_is_limited_by_peak_phase_rms_not_sequence_rss():
    from protectlab.core import seq

    current = m.phase_limit(10, 10, 12)
    assert max(abs(current)) == pytest.approx(12)
    assert abs(seq(current)[0]) < 1e-12
