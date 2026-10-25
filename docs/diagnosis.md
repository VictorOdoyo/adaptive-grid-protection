# Diagnosis and fault location

The two-ended locator uses synchronized terminal phasors and the full coupled line
series-impedance matrix. Both terminal currents point into the line.

Let x be distance fraction from the left. With a single fault point and no line
shunt capacitance:
VL - VR + Z IR = x Z(IL+IR).
A real least-squares estimate solves for x; a residual reports mismatch to that
model. Low total fault current makes the estimate unavailable.

The fault-location-infeed study generates resistive ground faults with two sources,
then compares this method with compensated single-ended reactance location.
Remote infeed and fault resistance produce a retained single-ended bias.

## Other estimators

Reactance location uses Im(Zapparent)/Im(Zline) and requires observable line
reactance. Its assumptions restrict how fault resistance and infeed may enter.

The Takagi helper uses incremental current and a supervised imaginary denominator.
It is checked in its aligned radial limit. It is not claimed unbiased for every
remote-infeed, load-change or controlled-inverter condition.

Arrival-time location converts synchronized left/right wave arrival times using a
declared velocity. Clock skew becomes a distance-error bound. This helper has no
distributed-line wavefront detector or EMT propagation model behind it.

Sequence signatures report incremental magnitudes and fractions rather than
asserting universal fault-type thresholds. Voltage unbalance and negative-sequence
current observability are separate outputs.

A valid mathematical estimate is not automatically an identifiable or dynamically
stable physical diagnosis; inspect the assumptions and residuals.
