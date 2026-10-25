# Adaptive Grid Protection

[![Engineering checks](https://github.com/VictorOdoyo/adaptive-grid-protection/actions/workflows/ci.yml/badge.svg)](https://github.com/VictorOdoyo/adaptive-grid-protection/actions/workflows/ci.yml)

A research workbench for **fault diagnosis and relay protection in inverter-dominated
networks**. Coupled phase-network faults feed synthesized waveforms, instrument
transformers, sampled estimators, relay elements and breaker feedback.

**[Measured study gallery](docs/results.md)** · [27 experiments](docs/experiments.md) ·
[Model assumptions](docs/model.md) · [Replay and provenance](docs/reproducibility.md)

The flagship comparison retains a real protection failure: conventional pickup
misses a weak-source fault, while a separately certified adaptive group restores
selective isolation. Other cases deliberately preserve CT undermeasurement,
clipped ADC coverage loss and a controlled-inverter directional misoperation.

## Run

Python 3.11+:

```bash
python -m pip install -e ".[dev]"
protectlab list
protectlab run --case weak-source-adaptive --output outputs/adaptive
protectlab verify outputs/adaptive
```

Locked development environment:

```bash
uv sync --locked --extra dev
uv run pytest -q
uv run ruff check src tests examples
uv run ruff format --check src tests examples
```

Capture all studies once, then render without rerunning the models:

```bash
protectlab batch --data-only --output outputs/catalog
protectlab render outputs/catalog
protectlab verify outputs/catalog
protectlab replay outputs/adaptive/fields.npz --output outputs/replayed
```

Each report contains numeric NPZ arrays, parameters, source/environment provenance,
CSV tables, scientific figures, an HTML page and a SHA-256 manifest.

## Engineering capabilities

| Layer | Implemented methods | Evidence |
| --- | --- | --- |
| Fault networks | Coupled ABC matrices, explicit fault constraints, remote infeed, nonlinear inverter-current equilibrium | Independent AG/BC/BCG/ABCG sequence connections, KCL and complex-power balance |
| Measurement | RMS cosine phasors, causal filtering, ADC rails, streaming Fourier, joint harmonic/DC fitting, variable-projection frequency | Exact RL transient, known complex phasors, missing-window propagation |
| Instruments | Nonlinear CT excitation/flux, burden and initial flux, ratio/phase calibration | Linear limit, excitation-energy gradient, sample/refinement checks |
| Elements | Phase/earth overcurrent, directional memory, mho/quadrilateral distance, percentage differential, harmonic blocking | Characteristic limits, unobservable signals, stale/skewed channels |
| System logic | Breaker delay/failure, single-pole current-zero benchmark, reclose/synchronism checks, pilot messages | Selective feedback, fault reset, loss, latency, sequence and freshness guards |
| Adaptation | Topology keys, versioned atomic groups, envelope certificates, fault freeze | Rollback/staleness rejection and audited primary-backup margins |
| Analysis | Two-ended/Takagi/reactance location, linear/discrete coordination, sampled robustness, uncertainty | Remote-infeed bias, independently audited constraints and explicit miss denominators |

## Import primary-unit recordings

```bash
protectlab record-info examples/healthy-waveform.csv
protectlab record-replay examples/healthy-waveform.csv --pickup-a 100 --output outputs/record
```

The [waveform schema](docs/records.md) specifies calibrated volts, amperes, seconds
and quality flags. This CSV format is project-specific. It does not claim COMTRADE
compatibility. Offline record replay cannot change a supplied waveform after a
virtual trip.

## Read the methods

- [Conventions](docs/conventions.md), [network model](docs/model.md), [inverter controls](docs/inverters.md)
- [Waveforms](docs/waveforms.md), [instruments](docs/instruments.md), [sampled measurements](docs/measurement.md)
- [Relay elements](docs/elements.md), [breaker and pilot logic](docs/switchgear.md)
- [Coordination](docs/coordination.md), [adaptive settings](docs/adaptation.md), [diagnosis](docs/diagnosis.md)
- [Uncertainty](docs/uncertainty.md), [Python API](docs/api.md), [references](docs/references.md)

The feeder replay combines quasi-steady phasor equilibria with sampled waveforms.
It is **not a full converter-switching EMT model**. A separate RL circuit benchmark
does integrate an actual differential equation. Inverter policies are illustrative,
and a solved equilibrium does not establish dynamic stability. Protection settings
are research examples with explicit modeled envelopes, not field commissioning data.

MIT licensed. See [contributing](CONTRIBUTING.md) and [release notes](CHANGELOG.md).
