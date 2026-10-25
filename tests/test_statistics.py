from protectlab import statistics as m


def test_wilson_interval_handles_zero_and_all_successes_without_false_certainty():
    low, high = m.wilson(0, 100)
    assert low == 0 and 0 < high < 0.05
    low, high = m.wilson(100, 100)
    assert 0.95 < low < 1 and high == 1
