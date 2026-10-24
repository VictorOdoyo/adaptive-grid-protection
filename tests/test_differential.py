from protectlab import differential as m


def test_through_current_cancels_and_internal_fault_adds():
    assert m.quantities(100, -100)["operate_a"] == 0
    assert m.quantities(100, 80)["operate_a"] == 180
    assert m.quantities(100, -100)["restraint_a"] == 100
