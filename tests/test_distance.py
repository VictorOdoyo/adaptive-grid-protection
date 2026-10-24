import numpy as np

from protectlab import distance as m


def test_phase_loops_measure_line_impedance_and_block_zero_current():
    from protectlab.core import abc

    current = abc([0, 10, 0])
    z = 2 + 4j
    result = m.phase_loops(current * z, current)
    assert np.allclose(result["impedance_ohm"], z)
    assert not np.any(m.phase_loops(np.ones(3), np.zeros(3))["valid"])
