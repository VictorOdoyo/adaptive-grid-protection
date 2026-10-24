import numpy as np
import pytest

from protectlab import distance as m


def test_phase_loops_measure_line_impedance_and_block_zero_current():
    from protectlab.core import abc

    current = abc([0, 10, 0])
    z = 2 + 4j
    result = m.phase_loops(current * z, current)
    assert np.allclose(result["impedance_ohm"], z)
    assert not np.any(m.phase_loops(np.ones(3), np.zeros(3))["valid"])


def test_ground_compensation_recovers_distance_for_single_phase_fault():
    from protectlab.core import phase_matrix

    current = np.array([100 + 0j, 0, 0])
    z0, z1 = 3 + 9j, 1 + 3j
    voltage = phase_matrix([z0, z1, z1]) @ current * 0.6
    result = m.ground_loops(voltage, current, z0, z1)
    assert result["impedance_ohm"][0] == pytest.approx(0.6 * z1)


def test_mho_characteristic_has_forward_and_observability_supervision():
    reach = 2 + 5j
    assert m.mho(0.8 * reach, reach)
    assert not m.mho(1.2 * reach, reach)
    assert not m.mho(0, reach, valid=False)
    assert not m.mho(0.5 * reach, reach, forward=False)


def test_quadrilateral_can_extend_resistive_reach_without_reactive_overreach():
    vertices = [-1 + 0j, 8 + 0j, 8 + 5j, -1 + 5j]
    assert m.polygon(6 + 3j, vertices)
    assert not m.polygon(6 + 6j, vertices)
    with pytest.raises(ValueError):
        m.polygon(1, [0, 2 + 2j, 2, 2j])


def test_load_wedge_blocks_forward_and_reverse_load_but_not_reactive_fault():
    assert np.array_equal(m.load_encroachment([10 + 1j, -10 - 1j, 2 + 9j], 5), [True, True, False])


def test_distance_zones_keep_separate_reach_and_time():
    zones = m.Zones([4j, 8j], [0, 0.1])
    for _ in range(9):
        assert not np.any(zones.update(6j, 0.01))
    assert zones.update(6j, 0.01)[1]
    immediate = m.Zones([4j], [0])
    assert immediate.update(2j, 0.001)[0]


def test_swing_blinders_distinguish_slow_entry_from_fault_jump():
    slow = m.SwingBlock(10, 5, 0.04)
    for z in [12, 9, 8, 7, 6, 4]:
        blocked = slow.update(z, 0.02)
    assert blocked
    fast = m.SwingBlock(10, 5, 0.04)
    assert not fast.update(12, 0.001)
    assert not fast.update(3, 0.001)
