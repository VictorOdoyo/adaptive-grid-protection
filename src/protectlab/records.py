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


def replay(
    record,
    pickup_a=100,
    time_multiplier=0.03,
    curve="very",
    directional=True,
    maximum_torque_rad=1.2,
    memory_hold_s=0.6,
):
    from .core import seq
    from .directional import MemoryVoltage, torque
    from .measurement import dft
    from .overcurrent import InverseRelay

    quality = audit(record)
    if not quality["uniform"] or not quality["integer_cycle"]:
        raise ValueError("relay replay requires uniform nominal-cycle sampling")
    measured_i = dft(record.time_s, record.current_a, record.nominal_hz, quality=record.valid)
    measured_v = dft(record.time_s, record.voltage_v, record.nominal_hz, quality=record.valid)
    relay = InverseRelay(pickup_a, curve, time_multiplier)
    memory = MemoryVoltage(1.0, memory_hold_s)
    trip = np.zeros(len(record.time_s), bool)
    forward = np.zeros(len(record.time_s), bool)
    travel = np.zeros(len(record.time_s))
    for k in range(1, len(record.time_s)):
        dt = record.time_s[k] - record.time_s[k - 1]
        valid = bool(measured_i["valid"][k] and measured_v["valid"][k])
        v1 = seq(measured_v["phasor"][k])[1]
        i1 = seq(measured_i["phasor"][k])[1]
        pol = memory.update(v1, dt, valid)
        forward[k] = pol["valid"] and bool(torque(pol["voltage"], i1, maximum_torque_rad)["forward"])
        trip[k] = relay.update(
            float(np.max(abs(measured_i["phasor"][k]))), dt, valid, blocked=directional and not forward[k]
        )
        travel[k] = relay.travel
    indices = np.flatnonzero(trip)
    return {
        "trip": trip,
        "forward": forward,
        "travel": travel,
        "phasor_a": measured_i["phasor"],
        "valid": measured_i["valid"],
        "trip_time_s": None if not len(indices) else float(record.time_s[indices[0]]),
    }
