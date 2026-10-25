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


def test_csv_has_unit_labels_explicit_quality_and_platform_stable_lf(tmp_path):
    record = m.Record([0, 0.001], np.ones((2, 3)), np.ones((2, 3)) * 2, np.array([True, False]))
    path = m.write_csv(record, tmp_path / "wave.csv")
    text = path.read_bytes()
    assert b"ia_a" in text and b"va_v" in text
    assert b"\r\n" not in text
    assert text.splitlines()[-1].endswith(b",0")
