import numpy as np

from protectlab import directional as m


def test_directional_torque_reverses_with_current_orientation_and_blocks_dead_voltage():
    v = 100 + 0j
    i = 10 * np.exp(-0.7j)
    assert m.torque(v, i, 0.7)["forward"]
    assert m.torque(v, -i, 0.7)["reverse"]
    assert not m.torque(0, i, 0.7)["valid"]
