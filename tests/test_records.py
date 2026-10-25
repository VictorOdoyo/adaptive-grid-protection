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


def test_csv_roundtrip_preserves_primary_phases_and_flags(tmp_path):
    rng = np.random.default_rng(2)
    record = m.Record(
        np.arange(100) / 3200, rng.normal(size=(100, 3)), rng.normal(size=(100, 3)), np.arange(100) % 10 != 0
    )
    restored = m.read_csv(m.write_csv(record, tmp_path / "record.csv"))
    assert np.array_equal(restored.current_a, record.current_a)
    assert np.array_equal(restored.voltage_v, record.voltage_v)
    assert np.array_equal(restored.valid, record.valid)


def test_import_audit_exposes_timestamp_gap_and_quality_loss():
    time = np.arange(100) / 3200
    time[50:] += 0.001
    record = m.Record(time, np.ones((100, 3)), np.ones((100, 3)), np.arange(100) != 20)
    audit = m.audit(record)
    assert not audit["uniform"]
    assert audit["valid_fraction"] == pytest.approx(0.99)


def test_imported_fault_replay_has_measured_detection_delay_and_invalid_quality_reset():
    from protectlab.core import abc
    from protectlab.waveforms import envelope, synthesize

    t = np.arange(2001) / 3200
    voltage = synthesize(t, abc([0, 230, 0]))
    current = synthesize(t, envelope(t, abc([0, 10, 0]), [(0.1, abc([0, 500 * np.exp(-1.2j), 0]))]))
    record = m.Record(t, voltage, current, np.ones(len(t), bool))
    result = m.replay(record)
    assert 0.1 < result["trip_time_s"] < 0.3
    bad = m.Record(t, voltage, current, np.zeros(len(t), bool))
    assert m.replay(bad)["trip_time_s"] is None


def test_dual_terminal_alignment_rejects_hidden_clock_shift():
    t = np.arange(100) / 3200
    a = m.Record(t, np.ones((100, 3)), np.ones((100, 3)), np.ones(100, bool))
    b = m.Record(t + 0.001, a.voltage_v, a.current_a, a.valid)
    with pytest.raises(ValueError, match="synchronized"):
        m.align(a, b)
    assert np.all(m.align(a, a)["valid"])


def test_record_report_marks_estimation_validity_and_uses_primary_units():
    from protectlab.core import abc
    from protectlab.waveforms import synthesize

    t = np.arange(400) / 3200
    record = m.Record(
        t, synthesize(t, abc([0, 230, 0])), synthesize(t, abc([0, 20, 0])), np.ones(len(t), bool)
    )
    result = m.report(record)
    assert result["parameters"]["primary_units"]
    assert result["summary"]["trip_time_s"] is None
