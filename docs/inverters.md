# Inverter fault-current policy

Inverter models are declared voltage-dependent current-reference policies.
They are not replicas of proprietary controls.

Positive-sequence current follows the local positive-sequence voltage angle.
The requested active component is specified in rated-current per unit.
Reactive support increases as positive-sequence voltage falls. Active or reactive
priority determines which component is preserved when the sequence-current budget
is exhausted.

An optional negative-sequence term opposes the local negative-sequence voltage.
Zero-sequence injection is zero in this three-wire policy. After combining sequences,
a final common scaling enforces the largest **phase RMS current** ceiling.
Limiting the root-sum-square of sequence magnitudes would not enforce each phase.

## Equilibrium and dynamics

The nonlinear network solve requires current references to agree with currents
injected into the solved nodal network. It reports both KCL and current-control
residuals. Nonconvergence raises an error instead of publishing the last iteration.

A separate causal first-order response helper can apply a held-current time
constant. The supplied feeder replay uses equilibrated current references; it does
not include this response as a coupled dynamic network state.

Current control can admit multiple equilibria in stressed conditions. Finding one
does not demonstrate its dynamic stability or reachability by a real inverter.

## Protection consequences

Low current can make load-security and fault-sensitivity pickup requirements
incompatible. Negative-sequence voltage need not provide usable negative-sequence
current. Conventional directional torque may also become misleading when controlled
current changes its phase relationship.

The directional-challenge experiment retains a sympathetic primary opening during
an upstream fault. Its result is a failure case, rather than an assertion that
memory polarization always restores correct direction.

See the [PNNL negative-sequence report](https://www.pnnl.gov/publications/impact-inverter-based-resources-grid-protection-review-negative-sequence-current)
for manufacturer/control dependence and the [references](references.md) for context.
