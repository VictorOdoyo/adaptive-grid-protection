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
