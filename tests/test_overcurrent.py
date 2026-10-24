import numpy as np
import pytest

from protectlab import overcurrent as m


def test_inverse_curves_match_published_scalar_anchor_and_pickup_limit():
    assert m.operating_time(2, "very", 0.1) == pytest.approx(1.35)
    assert np.isinf(m.operating_time(1))
    assert m.operating_time(10, "extreme", 0.2) == pytest.approx(16 / 99)


def test_relay_travel_matches_constant_current_time_and_resets_invalid_history():
    relay = m.InverseRelay(100, "very", 0.01)
    for _ in range(134):
        assert not relay.update(200, 0.001)
    assert relay.update(200, 0.001)
    other = m.InverseRelay(100)
    other.update(500, 0.01)
    assert other.travel > 0
    assert not other.update(500, 0.001, valid=False)
    assert other.travel == 0


def test_definite_relay_requires_persistent_pickup_and_respects_dropout():
    relay = m.DefiniteRelay(10, 0.03)
    assert not relay.update(11, 0.01)
    assert not relay.update(9.8, 0.01)
    assert relay.update(11, 0.01)
    assert relay.update(0, 0.01)
    relay = m.DefiniteRelay(10, 0.03)
    relay.update(11, 0.01)
    relay.update(9, 0.01)
    assert relay.elapsed == 0


def test_balanced_load_does_not_pick_up_residual_earth_element():
    from protectlab.core import abc

    result = m.phase_and_ground(abc([0, 100, 0]), 80, 10)
    assert result["phase_pickup"]
    assert not result["ground_pickup"]
    assert m.phase_and_ground([100, 0, 0], 150, 20)["ground_pickup"]
