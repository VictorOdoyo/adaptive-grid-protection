# Phase-network and feeder model

The network assembles coupled 3x3 branch admittances into a nodal ABC matrix.
Conventional sources are Norton equivalents of RMS Thevenin voltages behind full
phase impedance matrices. Loads in the supplied feeder are grounded 300 ohm
per-phase shunts. External APIs accept other passive admittance matrices.

Branches require reciprocal invertible impedance with passive resistance.
Source matrices may have unequal positive- and negative-sequence impedances;
a rotating-source equivalent need not be phase-domain reciprocal. Its Hermitian
resistive part must still be passive.

## Fault constraints

A connection matrix F maps nodal voltages to fault-loop voltage drops. The augmented
problem is [Y F^T; F -R] [V; If] = [J;0]. Zero R enforces a bolted constraint
without a huge artificial shunt admittance.

AG/BG/CG connect one phase to ground. AB/BC/CA bridge two phases through the specified
resistance. ABG/BCG/CAG use separate phase-to-ground resistors, not a shared ground
resistor. ABCG is a grounded resistive star. ABC is an ungrounded star; its two
independent loop resistances use Rf F F^T so phase resistors remain physically
symmetric. Bolted ABC/ABCG coincide for a balanced source.

Independent sequence references implement AG, BC, BCG and ABCG conventional-source
connections. The BCG reference uses a common ground path, so its cross-check against
separate phase resistors is restricted to the bolted case.

## Feeder

Three buses are source, junction and load. Positive-sequence line impedances are
0.2+j0.6 and 0.4+j1.2 ohm; zero-sequence values are 0.5+j1.5 and 1.2+j3.6 ohm.
The source has Z1=Z2=0.3+j1 and Z0=0.5+j3 ohm, scaled by source_factor.
An illustrative remote inverter is connected at load.

The primary breaker protects the junction-to-load line. Backup is upstream.
Every changed fault/breaker configuration recomputes the electrical equilibrium.
Disconnected grid-following islands without a voltage-forming source are explicitly
deenergized. They are not assigned a fictitious nominal voltage.

KCL residual, inverter-control residual and complex-power balance are distinct
checks. A small algebraic residual does not establish validity of the source model.

The replay is a sequence of quasi-steady network states. DC transients are separately
synthesized; there is no claim of distributed electromagnetic line dynamics,
converter switching or validated island dynamics.
