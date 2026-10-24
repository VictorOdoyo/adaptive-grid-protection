import numpy as np
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


def test_breaker_failure_requires_persistent_current_after_trip():
    failure = m.BreakerFailure(0.1, 10)
    assert not failure.update(0, True, 100)
    assert not failure.update(0.09, False, 100)
    assert failure.update(0.1, False, 100)
    clear = m.BreakerFailure(0.1, 10)
    clear.update(0, True, 100)
    assert not clear.update(0.05, False, 0, False)
    assert not clear.update(0.2, False, 0, False)


def test_arc_pole_waits_for_current_zero_after_contact_motion():
    pole = m.ArcPole(0.03)
    assert pole.update(0, 100, True)
    assert pole.update(0.02, -100)
    assert pole.update(0.031, -50)
    assert not pole.update(0.04, 2)


def test_sync_check_blocks_live_bus_phase_and_frequency_mismatch():
    assert m.sync_check(230, 230 * np.exp(0.1j), 50, 50.05)
    assert not m.sync_check(230, -230, 50, 50)
    assert not m.sync_check(230, 230, 50, 50.5)
    assert not m.sync_check(0, 230, 50, 50)
