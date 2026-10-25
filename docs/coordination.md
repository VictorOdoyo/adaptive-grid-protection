# Coordination

For fixed current pickups, inverse-time operation is linear in each relay's time
multiplier. The optimizer minimizes a positive weighted sum of multipliers while
enforcing primary-backup margins on each modeled fault.

For a pair, tbackup - tprimary - tprimary_breaker >= grading.
The supplied defaults are a 40 ms primary breaker and a 200 ms grading margin.
Relay-local current may differ between primary and backup. Comparing two time
curves at equal current is only an illustration.

Every result is passed to a separately called margin audit. A successful optimizer
status alone is not accepted as coordination evidence.

## Limits

An unobservable relay at or below pickup cannot be rescued by time multiplier
optimization. The API raises an error for such a constraint. Pickup feasibility
separately compares maximum-load security with minimum-fault sensitivity.

Continuous multiplier bounds and finite positive objective weights are explicit.
Discrete-setting search checks available levels after rounding rather than assuming
a continuously feasible solution remains feasible on hardware setting steps.
Search size is bounded.

## Robustness

robust_optimize expands the constraints across all supplied current samples.
The robust study includes 0.6 correlation between local relay-current perturbations.
It compares nominal and sample-envelope settings on the same saved draws.

This is sampled robustness, not a certificate over an unbounded continuous
uncertainty set. Changes in grounding, topology, inverter control or source strength
outside the modeled envelope need another study.

A setting certificate stores the exact group digest, current matrix, relay pairs,
grading and breaker assumptions, plus independently recomputed margins.
It is an unsigned reproducibility record, not manufacturer approval or a field
commissioning certificate.
