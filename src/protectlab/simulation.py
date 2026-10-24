from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class Scenario:
    fault_kind: str = "abcg"
    fault_bus: str = "load"
    resistance_ohm: float = 0.2
    source_factor: float = 1.0
    inverter_current_a: float = 50.0
    inverter_limit_pu: float = 1.2
    negative_gain: float = 0.0
    duration_s: float = 0.8
    inception_s: float = 0.12
    removal_s: float | None = None
    sample_hz: int = 3200
    frequency_hz: float = 50.0
    opening_s: float = 0.04
    primary_stuck: bool = False
    adaptive: bool = False
    instrumented: bool = False
    ct_knee_vs: float = 0.4
    adc_scale_a: float = 20.0
    noise_a: float = 0.0
    dc_tau_s: float = 0.0
    seed: int = 42

    def __post_init__(self):
        from .core import integer, positive

        if self.fault_kind not in (
            "none",
            "ag",
            "bg",
            "cg",
            "ab",
            "bc",
            "ca",
            "abg",
            "bcg",
            "cag",
            "abc",
            "abcg",
        ):
            raise ValueError("unknown fault kind")
        if self.fault_bus not in ("load", "junction"):
            raise ValueError("fault bus must be load or junction")
        for name in (
            "source_factor",
            "duration_s",
            "frequency_hz",
            "ct_knee_vs",
            "adc_scale_a",
            "inverter_limit_pu",
        ):
            positive(getattr(self, name), name)
        for name in (
            "resistance_ohm",
            "inverter_current_a",
            "negative_gain",
            "opening_s",
            "noise_a",
            "dc_tau_s",
        ):
            positive(getattr(self, name), name, allow_zero=True)
        integer(self.sample_hz, 200)
        integer(self.seed, 0)
        if self.seed >= 2**32 or not 0 < self.inception_s < self.duration_s:
            raise ValueError("valid seed and fault inception inside capture required")
        if self.removal_s is not None and not self.inception_s < self.removal_s < self.duration_s:
            raise ValueError("fault removal must follow inception inside capture")
        cycle = self.sample_hz / self.frequency_hz
        if abs(cycle - round(cycle)) > 1e-9 or cycle < 8:
            raise ValueError("at least eight integer samples per nominal cycle required")
        if any(type(getattr(self, k)) is not bool for k in ("adaptive", "instrumented", "primary_stuck")):
            raise ValueError("scenario switches must be boolean")

    def to_dict(self):
        return asdict(self)


def feeder(scenario, primary_closed=True, backup_closed=True):
    from .core import phase_matrix
    from .inverters import Inverter
    from .network import Branch, balanced_source

    buses = ("source", "junction", "load")
    sources = [
        balanced_source(
            "grid",
            "source",
            11000 / np.sqrt(3),
            scenario.source_factor * (0.5 + 3j),
            scenario.source_factor * (0.3 + 1j),
        )
    ]
    branches = [
        Branch(
            "backup", "source", "junction", phase_matrix([0.5 + 1.5j, 0.2 + 0.6j, 0.2 + 0.6j]), backup_closed
        ),
        Branch(
            "primary", "junction", "load", phase_matrix([1.2 + 3.6j, 0.4 + 1.2j, 0.4 + 1.2j]), primary_closed
        ),
    ]
    shunts = {"load": np.eye(3) / 300}
    inverters = (
        []
        if scenario.inverter_current_a == 0
        else [
            Inverter(
                "pv",
                "load",
                scenario.inverter_current_a,
                11000 / np.sqrt(3),
                limit_pu=scenario.inverter_limit_pu,
                negative_gain=scenario.negative_gain,
            )
        ]
    )
    return {
        "buses": buses,
        "branches": branches,
        "sources": sources,
        "shunts": shunts,
        "inverters": inverters,
    }
