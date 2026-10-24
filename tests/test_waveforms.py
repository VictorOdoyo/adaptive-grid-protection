import numpy as np
import pytest

from protectlab import waveforms as m


def test_rms_synthesis_has_correct_peak_and_phase():
    from protectlab.core import abc

    t = np.arange(320) / 16000
    wave = m.synthesize(t, abc([0, 10, 0]))
    assert wave[0, 0] == pytest.approx(np.sqrt(2) * 10)
    assert np.sqrt(np.mean(wave[:, 0] ** 2)) == pytest.approx(10)


def test_event_envelope_changes_at_event_sample():
    e = m.envelope([0, 0.01, 0.02], [1, 1, 1], [(0.01, [2, 3, 4])])
    assert np.array_equal(e[0], [1, 1, 1])
    assert np.array_equal(e[1], [2, 3, 4])


def test_fault_offset_cancels_ac_jump_at_inception():
    t = np.array([0.019, 0.02, 0.021])
    before = np.array([1, 2, 3], complex)
    after = before * 10
    offset = m.dc_offset(t, before, after, 0.02, 0.03)
    assert np.allclose(m.synthesize(t, after)[1] + offset[1], m.synthesize(t, before)[1])
