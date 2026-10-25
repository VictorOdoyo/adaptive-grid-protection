# Python API

For an end-to-end feeder:

```python
from protectlab.simulation import Scenario, run
result = run(Scenario(source_factor=20, adaptive=True))
print(result["events"])
```

For a custom conventional source and fault:

```python
from protectlab.network import balanced_source, fault_connection, solve, currents
source = balanced_source("grid", "bus", 6350, 3+8j, 1+3j)
fault = fault_connection(["bus"], "bus", "ag", resistance_ohm=1)
result = solve(["bus"], [], [source], fault=fault)
print(currents(result, [], [source])["sources"]["grid"])
```

For a reproducible catalog result:

```python
from protectlab.experiments import ExperimentConfig, run
from protectlab.reporting import write_report
result = run(ExperimentConfig("fault-location-infeed", 1, 42))
write_report(result, "outputs/location")
```

The [custom fault example](../examples/custom_fault.py) demonstrates an independent
sequence reference and a complex-power audit. The
[record generator](../examples/generate_record.py) writes the documented waveform CSV.

| Module | Purpose |
| --- | --- |
| core, network | RMS/sequence conventions, phase matrices, fault constraints, energized connectivity |
| inverters, simulation | Current policies and nonlinear equilibria, sampled feedback feeder |
| waveforms, instrument, frontend | Signal generation, CT flux, analog filtering, ADC |
| measurement, records | Fourier/joint fitting, primary-unit CSV, waveform replay |
| overcurrent, directional, distance, differential | Protection element algorithms and supervision |
| switchgear, communication, events | Breaker/reclose timing, simulated pilot channels, deterministic events |
| coordination, adaptive | Audited continuous/discrete setting optimization and transactional groups |
| diagnostics, statistics | Fault location, frequency estimation and uncertainty/scoring |
| results, reporting, experiments, batch | Validated evidence, archives, rendering and strict study requests |

Current limits, validity and missing operations are explicit outputs.
Lower-level APIs expose more physical parameters than the catalog's deliberately
small request schema. Capture changed physical assumptions in result parameters
when adding a custom study.
