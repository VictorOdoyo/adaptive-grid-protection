import pytest

from protectlab import simulation as m


def test_scenario_rejects_ambiguous_sample_rate_and_fault_chronology():
    with pytest.raises(ValueError):
        m.Scenario(sample_hz=3201)
    with pytest.raises(ValueError):
        m.Scenario(removal_s=0.01)
    with pytest.raises(ValueError):
        m.Scenario(adaptive=1)
