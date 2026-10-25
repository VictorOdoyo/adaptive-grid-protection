# Uncertainty and scoring

Classification keeps true positives, misses, false trips and secure nonoperations
as separate counts. A fault with unavailable measurements remains in the missed
protection denominator. Quality loss is also reported separately.

Sensitivity is TP/(TP+FN); security is TN/(TN+FP). An absent denominator is None,
not a perfect score. A deterministic hand-selected fault library is not an
independent random population from which universal reliability can be inferred.

Wilson intervals are provided for independent Bernoulli trials with stated
confidence. Zero successes and all successes retain finite uncertainty bounds.
The near-pickup study uses assumed independent normal current draws; it does not
estimate actual grid statistics.

Operating time diverges near pickup. Below pickup there is no finite operating
time. Arrays use an explicit observed mask and finite placeholders, while the
sensitivity denominator retains those nonoperations.

Bootstrap mean delay uses only operated trials and is labeled conditional on
operation. It is different from unit-to-unit population spread, and may be unstable
near a heavy timing tail. It must not be used to imply that missed faults clear.

The robust-coordination study uses correlated current samples from a declared
stress model. Certification covers those samples only. Systematic model error,
unknown inverter control, grounding changes and unmodeled instrument effects
require additional evidence.
