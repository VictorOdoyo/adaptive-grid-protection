"""Create an explicitly synthetic three-phase primary-unit CSV example."""

import argparse
from pathlib import Path

import numpy as np

from protectlab.core import abc
from protectlab.records import Record, write_csv
from protectlab.waveforms import envelope, synthesize


def generate(fault=False):
    duration = 0.6 if fault else 0.1
    time = np.arange(round(duration * 3200) + 1) / 3200
    initial = abc([0, 20 * np.exp(-0.35j), 0])
    events = [(0.12, abc([0, 500 * np.exp(-1.2j), 0]))] if fault else []
    current = synthesize(time, envelope(time, initial, events))
    voltage = synthesize(time, abc([0, 230, 0]))
    return Record(time, voltage, current, np.ones(len(time), bool))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fault", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("examples/healthy-waveform.csv"))
    args = parser.parse_args()
    print(write_csv(generate(args.fault), args.output))
