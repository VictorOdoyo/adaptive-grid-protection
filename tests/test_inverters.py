import numpy as np
import pytest

from protectlab import inverters as m


def test_reactive_priority_preserves_var_request_under_current_ceiling():
    i = m.priority_current(10, 8, 10)
    assert i == pytest.approx(6 - 8j)
    assert abs(m.priority_current(10, 8, 10, "active")) == pytest.approx(10)


def test_sequence_sum_is_limited_by_peak_phase_rms_not_sequence_rss():
    from protectlab.core import seq

    current = m.phase_limit(10, 10, 12)
    assert max(abs(current)) == pytest.approx(12)
    assert abs(seq(current)[0]) < 1e-12


def test_sag_requests_reactive_support_without_creating_zero_sequence():
    from protectlab.core import abc, seq

    inverter = m.Inverter("pv", "b", 100, 230)
    i = seq(m.requested_current(inverter, abc([0, 115, 0])))
    assert i[1].imag < -90
    assert max(abs(m.requested_current(inverter, abc([0, 5, 0])))) <= 120 + 1e-10


def test_ibr_network_satisfies_control_and_kcl_during_unbalanced_fault():
    from protectlab.network import Branch, balanced_source, fault_connection

    source = balanced_source("g", "a", 230, 1 + 3j, 0.5 + 1j)
    line = Branch("l", "a", "b", np.eye(3) * (0.2 + 0.4j))
    inverter = m.Inverter("pv", "b", 20, 230, negative_gain=0.2)
    fault = fault_connection(["a", "b"], "b", "ag", 0.5)
    result = m.solve_network(["a", "b"], [line], [source], [inverter], fault=fault)
    assert result["control_residual"] < 1e-7 and result["residual"] < 1e-10
    assert max(abs(result["inverter_current"]["pv"])) <= 24 + 1e-6
