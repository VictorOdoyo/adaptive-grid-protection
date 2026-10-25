# Waveform CSV

The exact UTF-8 header is:

```text
time_s,va_v,vb_v,vc_v,ia_a,ib_a,ic_a,valid
```

Time is seconds; voltage is instantaneous primary phase-to-ground volts; current
is instantaneous primary amperes into the protected line. valid is exactly 0 or 1.
All numeric samples are finite and timestamps strictly increase. The writer uses
LF and round-trip float representations.

The nominal frequency is supplied separately, default 50 Hz. Generic Record
objects can represent nonuniform time, but full-cycle relay replay requires
uniform sampling and an integer number of samples per nominal cycle.
record-info reports gaps and quality coverage before replay.

```bash
protectlab record-info examples/healthy-waveform.csv
protectlab record-replay examples/healthy-waveform.csv --pickup-a 100 --time-multiplier .03 --output outputs/record
protectlab verify outputs/record
```

The replay computes voltage/current Fourier windows, bounded memory direction
and inverse-time travel. It uses the supplied waveform and quality only.
The output retains the input file SHA-256 and source provenance.

A virtual trip does not alter recorded data or assert that a physical breaker
opened. For electrical interruption feedback, use the feeder simulation.

This is a project-specific schema, not a COMTRADE, IEC sampled-values or relay
manufacturer format. Calibrate CT/VT scaling, polarity and timestamp reference
before import; the parser does not guess them. Dual-terminal alignment rejects
clock mismatch rather than silently interpolating away synchronization errors.
