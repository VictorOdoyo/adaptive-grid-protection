# Experiment catalog

Run protectlab run --case NAME --output outputs/NAME. Defaults are scale 1, seed 42.
The [gallery](results.md) contains measured outputs and complete archived evidence.

| Case | Engineering question | Model level |
| --- | --- | --- |
| `strong-source` | Conventional selective feeder isolation | Sampled feeder with breaker feedback |
| `weak-source-static` | Missed pickup under reduced source strength | Sampled feeder with breaker feedback |
| `weak-source-adaptive` | Certified adaptive weak-source isolation | Sampled feeder with breaker feedback |
| `earth-fault-adaptive` | Ground fault with source grounding | Sampled feeder with breaker feedback |
| `phase-fault-adaptive` | Line-to-line fault isolation | Sampled feeder with breaker feedback |
| `instrumented-fault` | CT filter ADC and relay feedback | Sampled feeder with breaker feedback |
| `ct-saturation` | Saturated CT current undermeasurement | Sampled feeder with breaker feedback |
| `adc-clipping` | Unavailable clipped measurement windows | Sampled feeder with breaker feedback |
| `breaker-failure` | Stuck breaker and upstream backup | Sampled feeder with breaker feedback |
| `directional-challenge` | Controlled-inverter torque ambiguity | Sampled feeder with breaker feedback |
| `healthy-export` | Healthy reverse export security | Sampled feeder with breaker feedback |
| `temporary-fault` | Temporary fault and relay reset | Sampled feeder with breaker feedback |
| `fault-reference-benchmarks` | Independent phase and sequence fault references | Isolated analytical / policy benchmark |
| `inverter-current-ceilings` | Per-phase current-limiter allocation | Isolated analytical / policy benchmark |
| `negative-sequence-observability` | Control-dependent negative sequence | Isolated analytical / policy benchmark |
| `dc-offset-rejection` | Mimic phase correction on an RL transient | Isolated analytical / policy benchmark |
| `off-nominal-estimation` | Variable-projection frequency estimation | Isolated analytical / policy benchmark |
| `ct-burden-sensitivity` | Burden-dependent CT flux distortion | Isolated analytical / policy benchmark |
| `coordination-optimization` | Audited inverse-time coordination | Isolated analytical / policy benchmark |
| `robust-coordination` | Correlated current-envelope coordination | Isolated analytical / policy benchmark |
| `differential-security` | Restraint and harmonic supervision | Isolated analytical / policy benchmark |
| `distance-resistive-reach` | Resistive mho and quadrilateral reach | Isolated analytical / policy benchmark |
| `fault-location-infeed` | Two-ended location with remote infeed | Isolated analytical / policy benchmark |
| `pilot-channel-latency` | Pilot latency loss and stale permissions | Isolated analytical / policy benchmark |
| `adaptive-transition-guards` | Fault freeze during setting transitions | Isolated analytical / policy benchmark |
| `current-zero-interruption` | Contact parting and current-zero delay | Isolated analytical / policy benchmark |
| `pickup-uncertainty` | Sensitivity and conditional timing uncertainty | Isolated analytical / policy benchmark |

Cases are not all expected to succeed. weak-source-static and adc-clipping preserve
missed protection. directional-challenge preserves an unnecessary primary opening.
A green software test means that the documented behavior, including these failures,
was reproduced.

The feeder scores expected open devices only after replay. Expected labels do not
enter relay logic. Breaker-failure expects upstream interruption because the
primary breaker is stuck. Temporary-fault expects no breaker opening after the
external fault is removed.

The analytical studies isolate estimator, relay-characteristic, synchronization or
optimization behavior. They must not be interpreted as complete closed-loop EMT
simulations. Uncertainty distributions and binary pilot/policy stimuli are explicitly
assumed and recorded.

Resolution scale changes physical sample/sweep density, not the expected outcome
labels. It can expose time-step sensitivity and instrument integration error.
Do not treat deterministic fault-library pass fractions as measured population
reliability or standards acceptance.
