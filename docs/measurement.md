# Sampled measurements

The full-cycle estimator returns sqrt(2)/N times the sum of real samples multiplied
by exp(-i omega t). Timestamps use one absolute cosine phase reference. An integer
number of uniformly sampled nominal cycles is required.

The first N-1 estimates are unavailable. Any bad sample invalidates every window
containing it. Rolling implementation work is constant per channel and its complex
sum is periodically recomputed from retained samples to limit accumulated roundoff.
Batch and streaming implementations are checked independently.

True sliding RMS includes DC and harmonics. Fundamental RMS phasor magnitude does
not. Harmonic distortion ratios require an observable fundamental; a zero denominator
produces a validity flag rather than a fabricated distortion ratio.

## Transients and frequency

The mimic filter cancels a chosen exponential decay. Its sine-wave response has
phase as well as magnitude; comparisons remove that known complex response.
An incorrect decay constant does not guarantee cancellation.

Joint least squares fits DC and selected harmonic sine/cosine columns at actual
sample times. Variable projection searches a bounded frequency interval while
solving those linear coefficients. It estimates frequency from the record rather
than receiving the true frequency from the study generator.

The frequency fit is offline. A separate incremental phasor-angle helper estimates
frequency change relative to the nominal reference and blocks low-amplitude intervals.
No utility-grade PLL, ROCOF certification or arbitrary waveform identifiability is claimed.

The measurement frontend is causal. It filters secondary current before ADC
quantization and rail checks. Recorded CSV replay assumes supplied channels have
already passed whatever physical analog front end produced them.
