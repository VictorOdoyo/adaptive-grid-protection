import pytest

from protectlab import switchgear as m


def test_breaker_opens_after_latched_command_without_requiring_sustained_trip():
    b = m.Breaker(0.04)
    assert b.update(0.1, True)
    assert b.update(0.139)
    assert not b.update(0.14)
    assert b.open_time == pytest.approx(0.14)
    assert not b.close(0.2)
    assert b.close(0.2, True)
