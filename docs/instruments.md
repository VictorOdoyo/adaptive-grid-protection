# Instruments and analog input

The CT equivalent refers primary current to its secondary through a ratio.
Secondary current is referred primary current minus magnetizing current.
Secondary flux linkage obeys d(lambda)/dt = Rburden Isecondary.

The excitation curve is continuous and odd: lambda/Lm below a flux knee, followed
by a steeper slope 1/Lsat above it. An implicit monotone piecewise-linear update
keeps the nonlinear state bounded. The streaming state matches complete-record
integration on the same samples.

Magnetic energy is the integral of magnetizing current with respect to flux linkage.
An independent audit separates source work, burden dissipation, storage change and
numerical integration defect. Finite-step backward-Euler loss is not presented as
physical core loss.

This model has no hysteresis loop, frequency-dependent iron loss, winding leakage,
manufacturer excitation table or CT accuracy-class certification.
An initial flux state can stress the model but is not a validated remanence law.

## Range and calibration

Ratio/phase/polarity calibration is explicit. Recorded CSV channels must already
be calibrated to primary volts/amperes. The feeder's CurrentFrontend instead models
the CT secondary and converts estimated current back to primary units.

The ADC uses symmetric rails and 2 to 24 bits. It reports clipping separately from
quantized values. Any clipped phase invalidates that full-cycle relay window.
The normal instrumented example uses a 40 A secondary peak rail to accommodate
its chosen DC-offset fault. The adc-clipping case deliberately uses an inadequate
range and reports lost protection coverage.

A causal second-order Butterworth filter precedes the feeder ADC/Fourier estimator
at the configured sampling rate. The generic anti-alias/decimation utility provides
an explicit cutoff below the reduced Nyquist frequency. These are numerical
measurement models, not a designed or calibrated analog relay input card.
