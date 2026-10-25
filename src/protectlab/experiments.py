"""Validated reproducible run requests and lazy study dispatch."""

import json
from dataclasses import dataclass
from pathlib import Path

CASES = {
    "strong-source": ["studies_feeder", "strong", "Conventional selective feeder isolation"],
    "weak-source-static": ["studies_feeder", "weak_static", "Missed pickup under reduced source strength"],
    "weak-source-adaptive": ["studies_feeder", "weak_adaptive", "Certified adaptive weak-source isolation"],
    "earth-fault-adaptive": ["studies_feeder", "earth", "Ground fault with source grounding"],
    "phase-fault-adaptive": ["studies_feeder", "phase_fault", "Line-to-line fault isolation"],
    "instrumented-fault": ["studies_feeder", "instrumented", "CT filter ADC and relay feedback"],
    "ct-saturation": ["studies_feeder", "saturation", "Saturated CT current undermeasurement"],
    "adc-clipping": ["studies_feeder", "clipping", "Unavailable clipped measurement windows"],
    "breaker-failure": ["studies_feeder", "breaker_failure", "Stuck breaker and upstream backup"],
    "directional-challenge": ["studies_feeder", "reverse_infeed", "Controlled-inverter torque ambiguity"],
    "healthy-export": ["studies_feeder", "healthy", "Healthy reverse export security"],
    "temporary-fault": ["studies_feeder", "temporary", "Temporary fault and relay reset"],
    "fault-reference-benchmarks": [
        "studies_analysis",
        "fault_references",
        "Independent phase and sequence fault references",
    ],
    "inverter-current-ceilings": [
        "studies_analysis",
        "inverter_limits",
        "Per-phase current-limiter allocation",
    ],
    "negative-sequence-observability": [
        "studies_analysis",
        "negative_sequence",
        "Control-dependent negative sequence",
    ],
    "dc-offset-rejection": ["studies_analysis", "dc_rejection", "Mimic phase correction on an RL transient"],
    "off-nominal-estimation": ["studies_analysis", "off_nominal", "Variable-projection frequency estimation"],
    "ct-burden-sensitivity": ["studies_analysis", "ct_burden", "Burden-dependent CT flux distortion"],
    "coordination-optimization": ["studies_analysis", "coordination", "Audited inverse-time coordination"],
    "robust-coordination": [
        "studies_analysis",
        "robust_coordination",
        "Correlated current-envelope coordination",
    ],
    "differential-security": [
        "studies_analysis",
        "differential_security",
        "Restraint and harmonic supervision",
    ],
    "distance-resistive-reach": [
        "studies_analysis",
        "distance_reach",
        "Resistive mho and quadrilateral reach",
    ],
    "fault-location-infeed": ["studies_analysis", "fault_location", "Two-ended location with remote infeed"],
    "pilot-channel-latency": [
        "studies_analysis",
        "pilot_latency",
        "Pilot latency loss and stale permissions",
    ],
    "adaptive-transition-guards": [
        "studies_analysis",
        "adaptive_guard",
        "Fault freeze during setting transitions",
    ],
    "current-zero-interruption": [
        "studies_analysis",
        "current_zero",
        "Contact parting and current-zero delay",
    ],
    "pickup-uncertainty": [
        "studies_analysis",
        "pickup_uncertainty",
        "Sensitivity and conditional timing uncertainty",
    ],
}


@dataclass(frozen=True)
class ExperimentConfig:
    case: str = "strong-source"
    resolution_scale: int = 1
    seed: int = 42

    def __post_init__(self):
        if not isinstance(self.case, str) or self.case not in CASES:
            raise ValueError("unknown experiment case")
        if type(self.resolution_scale) is not int or not 1 <= self.resolution_scale <= 3:
            raise ValueError("resolution_scale must be an integer from 1 to 3")
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError("seed must be an integer in [0, 2**32)")

    def to_dict(self):
        return {"case": self.case, "resolution_scale": self.resolution_scale, "seed": self.seed}

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict) or set(value) - {"case", "resolution_scale", "seed"}:
            raise ValueError("request must be an object containing only case, resolution_scale and seed")
        return cls(**value)


def load_config(path):
    return ExperimentConfig.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
