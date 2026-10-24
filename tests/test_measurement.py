import numpy as np

from protectlab import measurement as m


def test_adc_reports_rails_and_half_lsb_error():
    v = np.array([-20, -2.1, 0, 3.2, 20])
    r = m.adc(v, 10, 12)
    assert np.array_equal(r["clipped"], [True, False, False, False, True])
    assert np.max(abs(r["values"][1:4] - v[1:4])) <= r["step"] / 2 + 1e-12
