import numpy as np
import pytest

from protectlab import simulation as m


def test_scenario_rejects_ambiguous_sample_rate_and_fault_chronology():
    with pytest.raises(ValueError):
        m.Scenario(sample_hz=3201)
    with pytest.raises(ValueError):
        m.Scenario(removal_s=0.01)
    with pytest.raises(ValueError):
        m.Scenario(adaptive=1)


def test_feeder_has_physical_load_and_separate_protected_breakers():
    grid = m.feeder(m.Scenario())
    assert [b.name for b in grid["branches"]] == ["backup", "primary"]
    assert grid["shunts"]["load"][0, 0] == pytest.approx(1 / 300)
    assert len(grid["inverters"]) == 1


def test_equilibrium_recalculates_fault_and_deenergizes_after_primary_trip():
    scenario = m.Scenario()
    fault = m.equilibrium(scenario, fault_active=True)
    assert max(abs(fault["branch_current"]["primary"])) > 400
    opened = m.equilibrium(scenario, primary_closed=False, fault_active=True)
    assert np.all(opened["voltage"]["load"] == 0)
    assert np.all(opened["branch_current"]["primary"] == 0)
    assert abs(opened["voltage"]["junction"][0]) > 6000


def test_closed_loop_primary_clears_fault_without_upstream_trip():
    result = m.run(m.Scenario(inverter_current_a=0, duration_s=0.5))
    assert any(e["event"] == "open" and e["device"] == "primary" for e in result["events"])
    assert not any(e["event"] == "trip" and e["device"] == "backup" for e in result["events"])
    assert np.all(result["final_voltage"]["load"] == 0)
    assert abs(result["final_voltage"]["junction"][0]) > 6000
    trip = next(e["time_s"] for e in result["events"] if e["event"] == "trip")
    opened = next(e["time_s"] for e in result["events"] if e["event"] == "open")
    assert opened - trip == pytest.approx(0.04, abs=1 / 3200)


def test_adc_clipping_blocks_closed_loop_trip_instead_of_using_fake_phasor():
    result = m.run(m.Scenario(instrumented=True, adc_scale_a=0.05, duration_s=0.4))
    assert np.any(result["adc_clipped"])
    assert not np.any(result["valid"][500:, 0])
    assert not any(e["event"] == "trip" for e in result["events"])


def test_dc_offset_changes_measured_fault_window_and_stops_after_opening():
    scenario = m.Scenario(dc_tau_s=0.04, duration_s=0.5)
    result = m.run(scenario)
    plain = m.run(m.Scenario(duration_s=0.5))
    assert np.max(abs(result["current_wave_a"] - plain["current_wave_a"])) > 100
    opened = next(e["time_s"] for e in result["events"] if e["event"] == "open")
    after = result["time_s"] > opened + 1 / scenario.sample_hz
    assert np.all(result["current_wave_a"][after, 0] == 0)
