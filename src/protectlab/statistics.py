import numpy as np


def wilson(successes, trials, confidence=0.95):
    from scipy.stats import norm

    from .core import integer

    integer(trials)
    integer(successes, 0)
    if successes > trials or not 0 < confidence < 1:
        raise ValueError("success count within trials and confidence in (0,1) required")
    z = float(norm.ppf((1 + confidence) / 2))
    p = successes / trials
    denominator = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / denominator
    half = z * np.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return (
        0.0 if successes == 0 else max(0.0, float(center - half)),
        1.0 if successes == trials else min(1.0, float(center + half)),
    )


def mean_interval(samples, confidence=0.95, resamples=2000, seed=42):
    from .core import finite, integer, stream

    values = finite(samples, real=True, ndim=1)
    integer(resamples, 100)
    if len(values) < 2 or not 0 < confidence < 1:
        raise ValueError("at least two independent samples and valid confidence required")
    rng = stream(seed, "clearing-mean-bootstrap")
    indices = rng.integers(0, len(values), (resamples, len(values)))
    means = np.mean(values[indices], axis=1)
    tail = (1 - confidence) / 2
    return tuple(float(v) for v in np.quantile(means, [tail, 1 - tail]))


def classification(actual_fault, tripped, available=None):
    fault = np.asarray(actual_fault)
    operation = np.asarray(tripped)
    quality = np.ones(fault.shape, bool) if available is None else np.asarray(available)
    if fault.ndim != 1 or operation.shape != fault.shape or quality.shape != fault.shape:
        raise ValueError("aligned trial labels required")
    if any(x.dtype != bool for x in (fault, operation, quality)) or len(fault) == 0:
        raise ValueError("nonempty boolean labels required")
    tp = int(np.sum(fault & operation))
    fn = int(np.sum(fault & ~operation))
    fp = int(np.sum(~fault & operation))
    tn = int(np.sum(~fault & ~operation))
    return {
        "true_positive": tp,
        "false_negative": fn,
        "false_positive": fp,
        "true_negative": tn,
        "unavailable": int(np.sum(~quality)),
        "sensitivity": None if tp + fn == 0 else tp / (tp + fn),
        "security": None if tn + fp == 0 else tn / (tn + fp),
    }
