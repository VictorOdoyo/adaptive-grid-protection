from protectlab import studies_analysis as m


def test_fault_reference_study_matches_all_independent_connections():
    result = m.fault_references()
    assert result["summary"]["maximum_relative_error"] < 1e-12
    assert len(result["tables"]["faults"]) == 4


def test_inverter_ceiling_study_limits_every_combined_phase():
    assert m.inverter_limits()["summary"]["limit_excess_a"] < 1e-10


def test_negative_sequence_study_reports_unobservable_zero_gain():
    result = m.negative_sequence()
    assert not result["summary"]["zero_gain_observable"]
    assert result["summary"]["full_gain_current_a"] > 1


def test_mimic_study_removes_matching_dc_without_hiding_filter_phase():
    result = m.dc_rejection()
    assert result["summary"]["maximum_valid_mimic_error"] < 1e-10
    assert result["summary"]["maximum_valid_raw_error"] > 0.01


def test_off_nominal_study_estimates_frequency_instead_of_reading_setup():
    result = m.off_nominal()
    assert result["summary"]["frequency_error_hz"] < 1e-5
    assert result["summary"]["fitted_phasor_relative_error"] < 1e-6


def test_ct_burden_study_shows_increased_saturation_exposure():
    result = m.ct_burden()
    assert (
        result["summary"]["high_burden_saturated_fraction"]
        > result["summary"]["low_burden_saturated_fraction"]
    )


def test_coordination_study_reports_audited_margin_not_only_optimizer_status():
    assert m.coordination()["summary"]["minimum_margin_s"] >= 0.2 - 1e-9


def test_robust_study_preserves_every_sample_margin():
    result = m.robust_coordination()
    assert result["summary"]["robust_settings_worst_margin_s"] >= 0.2 - 1e-9
    assert result["summary"]["nominal_settings_worst_margin_s"] < 0.2


def test_differential_security_study_avoids_external_ratio_error_pickups():
    result = m.differential_security()
    assert result["summary"]["external_false_pickups"] == 0
    assert result["summary"]["internal_pickups"] > 100


def test_quadrilateral_study_exposes_mho_resistive_underreach():
    result = m.distance_reach()
    assert result["summary"]["quadrilateral_detected_points"] > result["summary"]["mho_detected_points"]
