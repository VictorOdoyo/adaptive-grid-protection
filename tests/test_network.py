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
