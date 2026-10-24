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


def test_adaptive_group_covers_fault_envelope_before_activation():
    from protectlab.adaptive import commit

    manager = m.setting_manager(m.Scenario(source_factor=20, adaptive=True))
    assert manager.pending is not None
    topology = manager.pending["topology"]
    assert commit(manager, 0.03, topology, 0.03)
    assert manager.active.pickups_a == (80.0, 100.0)


def test_adaptive_settings_clear_weak_fault_that_conventional_pickup_misses():
    from dataclasses import replace

    weak = m.Scenario(source_factor=20, duration_s=0.8)
    conventional = m.run(weak)
    adaptive = m.run(replace(weak, adaptive=True))
    assert not any(e["event"] == "trip" for e in conventional["events"])
    assert any(e["device"] == "primary" and e["event"] == "open" for e in adaptive["events"])
    assert not any(e["device"] == "backup" and e["event"] == "trip" for e in adaptive["events"])
    assert adaptive["group_revision"][-1] == 2


def test_primary_opening_also_removes_upstream_fault_offset_tail():
    result = m.run(m.Scenario(dc_tau_s=0.04, duration_s=0.5))
    opened = next(e["time_s"] for e in result["events"] if e["event"] == "open")
    after = result["time_s"] > opened + 2 / 3200
    assert np.max(abs(result["current_wave_a"][after])) < 1e-6


def test_directional_supervision_exposes_inverter_torque_ambiguity_without_truth_gating():
    from dataclasses import replace

    scenario = m.Scenario(fault_bus="junction", inverter_current_a=1000, duration_s=0.8)
    directional = m.run(scenario)
    blind = m.run(replace(scenario, directional=False))
    before = (directional["time_s"] > 0.04) & (directional["time_s"] < scenario.inception_s)
    assert not np.any(directional["forward"][before, 0])

    def trip_time(result):
        return next(
            e["time_s"] for e in result["events"] if e["event"] == "trip" and e["device"] == "primary"
        )

    # Controlled-inverter fault current can defeat conventional torque interpretation.
    assert trip_time(directional) > trip_time(blind)
    assert any(e["event"] == "open" and e["device"] == "backup" for e in directional["events"])
