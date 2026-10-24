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
