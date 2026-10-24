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


def test_takagi_locator_matches_radial_aligned_fault_increment_limit():
    current = 100 * np.exp(-1j)
    pre = current * 0.1
    voltage = 0.7 * (1 + 3j) * current + 2 * current
    result = m.takagi(voltage, current, pre, 1 + 3j)
    assert result["fraction"] == pytest.approx(0.7)
    assert not m.takagi(1, 1, 1, 1j)["valid"]


def test_signature_reports_zero_sequence_and_blocks_tiny_increment():
    from protectlab.core import abc

    before = abc([0, 10, 0])
    result = m.signature([100, 100, 100], before + np.array([30, 0, 0]), [100, 100, 100], before)
    assert result["observable"]
    assert result["delta_i0_a"] == pytest.approx(10)
    assert not m.signature([1, 1, 1], before, [1, 1, 1], before)["observable"]


def test_arrival_location_and_clock_error_scale_with_wave_velocity():
    result = m.arrival_location(0.004, 0.006, 2e6, 2e8, 1e-6)
    assert result["position_m"] == pytest.approx(800000)
    assert result["clock_error_bound_m"] == pytest.approx(100)
