# Protection elements

## Overcurrent

Inverse-time curves use TMS [k/(M^alpha-1)+c], M=I/Ipickup. Six IEC/IEEE-style
coefficient families are implemented. At M<=1 operating time is infinite, not zero.
They are published formulas, not certification of a commercial relay implementation.

Travel integrates dt/toperate at each valid measured sample. Below pickup it resets
linearly at the stated reset time. Invalid or blocked measurements reset travel;
a trip is latched. Definite-time elements use pickup/dropout hysteresis and a
separate persistent timer. The reset law is explicit and is not a reproduction
of every standard's optional inverse reset behavior.

Residual earth pickup uses |Ia+Ib+Ic|. Voltage-restrained pickup is bounded by a
declared minimum fraction. It changes sensitivity but does not by itself establish
selectivity or distinguish a fault from a voltage-transformer failure.

## Directional

Torque is Re{Vpol conj(Iop) exp(-i MTA)}. Minimum voltage/current thresholds provide
observability. Memory voltage is valid for a bounded interval after collapse.
Expired memory is reset when a fresh sufficient voltage returns.

Negative-sequence direction uses opposing -V2 polarization; residual direction
uses opposing residual voltage. These signs and the terminal orientation are
explicit. Controlled inverter current can invalidate conventional direction
assumptions, as retained in the directional-challenge feeder case.

## Distance

Phase loops are Vab/Iab, Vbc/Ibc and Vca/Ica. Earth loops use
Va/[Ia+k0(Ia+Ib+Ic)], k0=(Z0-Z1)/(3Z1). Small loop current makes the result unavailable.

Mho, strictly convex polygon, load-encroachment wedges and independently delayed
zones are implemented. Invalid data resets zone timers. A simple concentric-blinder
swing blocker is an isolated timing model, not complete out-of-step protection.

## Differential

Operate current is |IL+IR| with both currents into the zone. Restraint is half the
sum of terminal magnitudes. Continuous dual slopes raise the threshold at high
through current. Ratio/clock and optional zero-sequence compensation are explicit.

Second-harmonic blocking has minimum fundamental observability and optional
cross-phase blocking. Clock compensation rotates positive and negative sequences in
opposite directions; retained zero sequence has no clock rotation. Grounding paths
must still be modeled explicitly. The freshness/skew supervisor blocks stale, future or
unsynchronized remote data. Static inrush blocking tests do not simulate transformer
energization physics.
