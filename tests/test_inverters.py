import pytest

from protectlab import inverters as m


def test_reactive_priority_preserves_var_request_under_current_ceiling():
    i = m.priority_current(10, 8, 10)
    assert i == pytest.approx(6 - 8j)
    assert abs(m.priority_current(10, 8, 10, "active")) == pytest.approx(10)
