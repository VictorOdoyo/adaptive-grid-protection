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
