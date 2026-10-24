import numpy as np


def quantities(left, right):
    from .core import finite

    left, right = np.broadcast_arrays(finite(left), finite(right))
    return {"operate_a": abs(left + right), "restraint_a": 0.5 * (abs(left) + abs(right))}
