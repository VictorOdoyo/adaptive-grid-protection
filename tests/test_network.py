import numpy as np
import pytest

from protectlab import network as m


def test_branch_rejects_nonpassive_and_nonreciprocal_impedance():
    with pytest.raises(ValueError):
        m.Branch("x", "a", "b", -np.eye(3))
    line = m.Branch("line", "a", "b", np.eye(3) * (1 + 2j))
    with pytest.raises(ValueError):
        line.z[0, 0] = 3


def test_source_emf_and_impedance_keep_grounded_zero_sequence():
    from protectlab.core import seq

    source = m.balanced_source("grid", "a", 6350, 3j, 1j)
    assert seq(source.emf)[1] == pytest.approx(6350)
    assert np.allclose(source.z @ np.ones(3), np.ones(3) * 3j)


def test_branch_stamp_has_gauge_nullspace_without_ground_source():
    line = m.Branch("line", "a", "b", np.eye(3) * (1 + 2j))
    y, j, _ = m.admittance(["a", "b"], [line])
    assert np.allclose(y @ np.ones(6), 0)
    assert np.all(j == 0)


def test_network_load_voltage_matches_independent_scalar_divider():
    source = m.balanced_source("grid", "a", 230, 1, 1)
    line = m.Branch("line", "a", "b", np.eye(3))
    result = m.solve(["a", "b"], [line], [source], {"b": np.eye(3) / 8})
    assert abs(result["voltage"]["b"][0]) == pytest.approx(184)
    assert result["residual"] < 1e-12


def test_bolted_single_ground_fault_matches_sequence_formula():
    from protectlab.core import seq

    source = m.balanced_source("g", "a", 230, 3 + 6j, 1 + 2j)
    result = m.solve(["a"], [], [source], fault=m.fault_connection(["a"], "a", "ag"))
    expected = 3 * 230 / ((3 + 6j) + 2 * (1 + 2j))
    assert result["fault_current"][0] == pytest.approx(expected)
    assert abs(result["voltage"]["a"][0]) < 1e-10
    assert np.allclose(seq(np.linalg.solve(source.z, source.emf - result["voltage"]["a"])), expected / 3)


def test_source_and_branch_currents_balance_loaded_terminal():
    source = m.balanced_source("g", "a", 230, 1j, 1j)
    line = m.Branch("l", "a", "b", np.eye(3) * (1 + 1j))
    result = m.solve(["a", "b"], [line], [source], {"b": np.eye(3) / 10})
    currents = m.currents(result, [line], [source])
    assert np.allclose(currents["sources"]["g"], currents["branches"]["l"])
    assert np.allclose(currents["branches"]["l"], result["voltage"]["b"] / 10)


def test_complex_power_balance_includes_finite_ground_fault_resistor():
    source = m.balanced_source("g", "a", 230, 1 + 2j, 1 + 2j)
    line = m.Branch("l", "a", "b", np.eye(3) * (0.2 + 0.4j))
    fault = m.fault_connection(["a", "b"], "b", "ag", 2)
    result = m.solve(["a", "b"], [line], [source], fault=fault)
    balance = m.power_balance(result, [line], [source], fault=fault)
    assert abs(balance["defect_va"]) < 1e-8
    assert balance["fault_w"] > 0


def test_line_split_preserves_unfaulted_terminal_solution():
    source = m.balanced_source("g", "a", 230, 1j, 1j)
    line = m.Branch("l", "a", "b", np.eye(3) * (1 + 2j))
    original = m.solve(["a", "b"], [line], [source], {"b": np.eye(3) / 10})
    buses, lines = m.split_line(["a", "b"], [line], "l", 0.37)
    divided = m.solve(buses, lines, [source], {"b": np.eye(3) / 10})
    assert np.allclose(original["voltage"]["b"], divided["voltage"]["b"])


def test_resistive_floating_star_three_phase_fault_matches_balanced_reference():
    source = m.balanced_source("g", "a", 230, 3 + 4j, 1 + 2j)
    fault = m.fault_connection(["a"], "a", "abc", 2)
    result = m.solve(["a"], [], [source], fault=fault)
    current = m.currents(result, [], [source])["sources"]["g"]
    assert current[0] == pytest.approx(230 / (3 + 2j))
    assert abs(m.power_balance(result, [], [source], fault=fault)["defect_va"]) < 1e-8


def test_open_breaker_separates_unenergized_downstream_bus():
    from dataclasses import replace

    source = m.balanced_source("g", "a", 230, 1j, 1j)
    branch = m.Branch("l", "a", "b", np.eye(3))
    assert m.energized(["a", "b"], [branch], [source]) == {"a", "b"}
    assert m.energized(["a", "b"], [replace(branch, closed=False)], [source]) == {"a"}


def test_post_trip_solver_does_not_fabricate_voltage_on_unsupported_island():
    source = m.balanced_source("g", "a", 230, 1j, 1j)
    line = m.Branch("l", "a", "b", np.eye(3), False)
    fault = m.fault_connection(["a", "b"], "b", "ag")
    result = m.solve_energized(["a", "b"], [line], [source], fault=fault)
    assert np.all(result["voltage"]["b"] == 0)
    assert abs(result["voltage"]["a"][0]) == pytest.approx(230)
    assert result["deenergized"] == ["b"]


def test_driving_point_impedance_adds_source_and_line_series_matrices():
    source = m.balanced_source("g", "a", 230, 3j, 1j)
    line = m.Branch("l", "a", "b", np.eye(3) * (1 + 2j))
    assert np.allclose(m.driving_impedance(["a", "b"], [line], [source], "b"), source.z + line.z)


@pytest.mark.parametrize("kind", ["ag", "bc", "bcg", "abcg"])
def test_phase_constraint_solver_matches_independent_sequence_connections(kind):
    source = m.balanced_source("g", "a", 230, 3 + 8j, 1 + 3j, 1.2 + 3.5j)
    # bcg reference uses common ground resistance; independent phase resistors coincide at zero.
    result = m.solve(["a"], [], [source], fault=m.fault_connection(["a"], "a", kind))
    phase = m.currents(result, [], [source])["sources"]["g"]
    expected = m.sequence_reference(230, 3 + 8j, 1 + 3j, 1.2 + 3.5j, kind)["phase_a"]
    assert np.allclose(phase, expected)


def test_duplicate_source_names_and_nonboolean_breakers_are_rejected():
    source = m.balanced_source("g", "a", 230, 1j, 1j)
    with pytest.raises(ValueError, match="source names"):
        m.admittance(["a"], [], [source, source])
    with pytest.raises(ValueError, match="boolean"):
        m.Branch("l", "a", "b", np.eye(3), closed="open")
