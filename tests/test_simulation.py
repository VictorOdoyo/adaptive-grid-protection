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
