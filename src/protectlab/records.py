from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Record:
    time_s: object
    voltage_v: object
    current_a: object
    valid: object
    nominal_hz: float = 50.0

    def __post_init__(self):
        from .core import finite, positive, timebase

        time = timebase(self.time_s).copy()
        voltage = finite(self.voltage_v, real=True).copy()
        current = finite(self.current_a, real=True).copy()
        valid = np.asarray(self.valid).copy()
        if (
            voltage.shape != (len(time), 3)
            or current.shape != voltage.shape
            or valid.shape != time.shape
            or valid.dtype != bool
        ):
            raise ValueError("three primary-unit channels and boolean quality per timestamp required")
        positive(self.nominal_hz)
        for name, value in (
            ("time_s", time),
            ("voltage_v", voltage),
            ("current_a", current),
            ("valid", valid),
        ):
            value.setflags(write=False)
            object.__setattr__(self, name, value)


COLUMNS = ("time_s", "va_v", "vb_v", "vc_v", "ia_a", "ib_a", "ic_a", "valid")


def write_csv(record, path):
    import csv
    from pathlib import Path

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(COLUMNS)
        for t, v, i, q in zip(record.time_s, record.voltage_v, record.current_a, record.valid, strict=True):
            writer.writerow(
                [repr(float(t)), *[repr(float(x)) for x in v], *[repr(float(x)) for x in i], int(q)]
            )
    return path


def read_csv(path, nominal_hz=50):
    import csv
    from pathlib import Path

    with Path(path).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(COLUMNS):
            raise ValueError("CSV must use exact primary-unit channel schema")
        rows = list(reader)
    if len(rows) < 2:
        raise ValueError("at least two waveform samples required")
    numeric = []
    for row in rows:
        if None in row or row["valid"] not in ("0", "1"):
            raise ValueError("complete samples and binary quality required")
        try:
            numeric.append([float(row[name]) for name in COLUMNS[:-1]])
        except (TypeError, ValueError) as error:
            raise ValueError("numeric waveform channels required") from error
    values = np.asarray(numeric)
    return Record(
        values[:, 0],
        values[:, 1:4],
        values[:, 4:7],
        np.array([row["valid"] == "1" for row in rows]),
        nominal_hz,
    )


def audit(record):
    dt = np.diff(record.time_s)
    spacing = float(np.mean(dt))
    uniform = bool(np.allclose(dt, spacing, rtol=1e-8, atol=spacing * 1e-10))
    cycle = 1 / (spacing * record.nominal_hz)
    return {
        "sample_hz": 1 / spacing,
        "uniform": uniform,
        "samples": len(record.time_s),
        "samples_per_cycle": cycle,
        "integer_cycle": abs(cycle - round(cycle)) < 1e-8,
        "valid_fraction": float(np.mean(record.valid)),
        "maximum_gap_s": float(np.max(dt)),
        "duration_s": float(record.time_s[-1] - record.time_s[0]),
    }
