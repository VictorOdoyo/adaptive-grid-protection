from protectlab import studies_feeder as m


def test_strong_source_replay_is_selective_and_preserves_healthy_junction():
    result = m.strong()
    assert result["summary"]["selective"]
    assert result["summary"]["final_junction_voltage_pu"] > 0.95
    assert result["summary"]["clearing_delay_s"] > 0.04
