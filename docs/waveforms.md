# Waveforms and replay timing

The feeder converts solved RMS phasors into three-phase cosine waveforms.
Faults and breaker operations change the phasor envelope. A configurable decaying
DC term cancels the instantaneous AC current jump at fault inception. Its time
constant is an explicit study parameter, not derived automatically from all
network impedances.

The DC term is removed from electrically interrupted paths. It is not allowed to
survive as a fictitious upstream fault-current tail after downstream isolation.

This envelope synthesis does not enforce every inductor/capacitor continuity
constraint in an arbitrary multiphase network. Breaker feedback recomputes the
post-event phasor state on the following sampled interval. Relay logic never reads
the scenario's fault label to decide whether to trip.

## Independent RL reference

rl_fault is the exact forced series-RL solution including its exponentially
decaying initial-condition component. rl_trapezoid independently integrates
L di/dt + R i = v(t) on actual timestamps.

Refinement tests verify the trapezoidal error against the exact solution.
This benchmark validates that circuit and the estimator transient tests. It does
not turn the separate feeder envelope model into a general EMT solver.

## Sampled timing

Base feeder rate is 3200 Hz at 50 Hz: 64 samples per cycle. resolution_scale
multiplies the rate and corresponding window size while preserving physical
durations and nominal frequency.

Trip time is the sample at which accumulated relay travel reaches its threshold.
Mechanical opening follows its own timer; fault clearing is not synonymous with
trip assertion. Current-zero interruption is a separate single-pole prospective
waveform benchmark with its own stated exclusions.

Gaussian noise uses deterministic named streams in absolute amperes.
Harmonic injection uses specified RMS components. Dropout keeps finite placeholders
and separate validity flags, never an invented healthy measurement.
