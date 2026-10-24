import numpy as np
import pytest

from protectlab import diagnostics as m


def test_two_ended_location_recovers_resistive_fault_with_remote_infeed():
    from protectlab.network import Branch, balanced_source, currents, fault_connection, solve, split_line

    source1 = balanced_source("left", "a", 230, 1j, 1j)
    source2 = balanced_source("right", "b", 230, 2j, 2j, angle_rad=0.03)
    line = Branch("l", "a", "b", np.eye(3) * (1 + 3j))
    buses, lines = split_line(["a", "b"], [line], "l", 0.63)
    solved = solve(buses, lines, [source1, source2], fault=fault_connection(buses, "fault", "ag", 2))
    c = currents(solved, lines)["branches"]
    result = m.two_ended(solved["voltage"]["a"], solved["voltage"]["b"], c["l__near"], -c["l__far"], line.z)
    assert result["valid"]
    assert result["fraction"] == pytest.approx(0.63)
    assert result["residual_v"] < 1e-10


def test_reactance_locator_ignores_pure_resistive_drop_in_its_stated_model():
    result = m.reactance_location(0.4 * (1 + 3j) + 2, 1 + 3j)
    assert result["fraction"] == pytest.approx(0.4)
    assert result["valid"]
