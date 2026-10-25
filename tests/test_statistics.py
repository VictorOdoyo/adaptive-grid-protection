import numpy as np

from protectlab import statistics as m


def test_wilson_interval_handles_zero_and_all_successes_without_false_certainty():
    low, high = m.wilson(0, 100)
    assert low == 0 and 0 < high < 0.05
    low, high = m.wilson(100, 100)
    assert 0.95 < low < 1 and high == 1


def test_mean_uncertainty_is_narrower_than_individual_clearing_variation():
    values = np.linspace(0.1, 0.3, 101)
    low, high = m.mean_interval(values)
    assert low < 0.2 < high
    assert high - low < 0.05
