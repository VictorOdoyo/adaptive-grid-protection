import numpy as np
import pytest

from protectlab import differential as m


def test_through_current_cancels_and_internal_fault_adds():
    assert m.quantities(100, -100)["operate_a"] == 0
    assert m.quantities(100, 80)["operate_a"] == 180
    assert m.quantities(100, -100)["restraint_a"] == 100


def test_percentage_restraint_secures_ratio_error_but_detects_internal_fault():
    assert not m.characteristic(1000, -900)["pickup"]
    assert m.characteristic(500, 400)["pickup"]
    q = m.characteristic([199, 201], [199, 201])
    assert q["threshold_a"][1] - q["threshold_a"][0] == pytest.approx(0.8)


def test_harmonic_blocking_does_not_turn_missing_fundamental_into_inrush():
    result = m.harmonic_block([100, 100, 0], [20, 1, 100])
    assert np.array_equal(result["blocked"], [True, False, False])
    assert not result["valid"][2]
    assert np.all(m.harmonic_block([100, 100, 100], [20, 1, 1], cross_phase=True)["blocked"])
