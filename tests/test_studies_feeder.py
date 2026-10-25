import numpy as np

from protectlab import studies_feeder as m


def test_strong_source_replay_is_selective_and_preserves_healthy_junction():
    result = m.strong()
    assert result["summary"]["selective"]
    assert result["summary"]["final_junction_voltage_pu"] > 0.95
    assert result["summary"]["clearing_delay_s"] > 0.04


def test_weak_source_static_case_reports_missed_protection_not_success():
    result = m.weak_static()
    assert not result["summary"]["selective"]
    assert not result["summary"]["required_isolation"]
    assert result["summary"]["clearing_delay_s"] is None


def test_weak_source_adaptation_restores_selective_interruption():
    result = m.weak_adaptive()
    assert result["summary"]["selective"]
    assert result["summary"]["clearing_delay_s"] < 0.5
    assert result["arrays"]["group_revision"][-1] == 2


def test_earth_fault_case_is_selective_with_unbalanced_phase_currents():
    result = m.earth()
    assert result["summary"]["selective"]
    fault = (result["arrays"]["time_s"] > 0.15) & (result["arrays"]["time_s"] < 0.18)
    current = result["arrays"]["true_current_a"][fault, 0]
    assert np.max(abs(current[:, 0])) > np.max(abs(current[:, 1])) * 1.5


def test_phase_fault_replay_is_selective_without_ground_fault_current():
    from protectlab.core import seq

    result = m.phase_fault()
    assert result["summary"]["selective"]
    current = result["arrays"]["true_current_a"][500, 0]
    assert abs(seq(current)[0]) < abs(seq(current)[1]) * 0.01
