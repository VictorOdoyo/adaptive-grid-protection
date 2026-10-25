from protectlab import studies_analysis as m


def test_fault_reference_study_matches_all_independent_connections():
    result = m.fault_references()
    assert result["summary"]["maximum_relative_error"] < 1e-12
    assert len(result["tables"]["faults"]) == 4


def test_inverter_ceiling_study_limits_every_combined_phase():
    assert m.inverter_limits()["summary"]["limit_excess_a"] < 1e-10
