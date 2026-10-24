import numpy as np

from protectlab import directional as m


def test_directional_torque_reverses_with_current_orientation_and_blocks_dead_voltage():
    v = 100 + 0j
    i = 10 * np.exp(-0.7j)
    assert m.torque(v, i, 0.7)["forward"]
    assert m.torque(v, -i, 0.7)["reverse"]
    assert not m.torque(0, i, 0.7)["valid"]


def test_memory_polarization_expires_after_close_in_voltage_collapse():
    memory = m.MemoryVoltage(20, 0.03)
    assert memory.update(100, 0.001)["valid"]
    assert memory.update(0, 0.01)["valid"]
    assert memory.update(0, 0.01)["valid"]
    assert not memory.update(0, 0.011)["valid"]


def test_negative_sequence_direction_requires_observable_negative_sequence():
    from protectlab.core import abc

    healthy = m.negative_sequence(abc([0, 100, 0]), abc([0, 10, 0]))
    assert not healthy["valid"]
    result = m.negative_sequence(abc([0, 100, -5]), abc([0, 10, np.exp(-1.2j)]))
    assert result["forward"]
