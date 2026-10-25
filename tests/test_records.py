import numpy as np
import pytest

from protectlab import records as m


def test_record_rejects_misaligned_samples_and_protects_input_snapshot():
    t = np.arange(100) / 3200
    current = np.ones((100, 3))
    record = m.Record(t, current, current, np.ones(100, bool))
    current[0] = 99
    assert record.current_a[0, 0] == 1
    with pytest.raises(ValueError):
        record.current_a[0] = 0
    with pytest.raises(ValueError):
        m.Record(t, current, current, np.ones(100))
