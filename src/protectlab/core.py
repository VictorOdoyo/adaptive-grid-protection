import numpy as np


def finite(value, *, real=False, ndim=None):
    array = np.asarray(value)
    if array.dtype.kind not in "biufc" or not np.all(np.isfinite(array)):
        raise ValueError("finite numeric values required")
    if real and np.iscomplexobj(array):
        raise ValueError("real values required")
    if ndim is not None and array.ndim != ndim:
        raise ValueError("incorrect array rank")
    return array.astype(float if real else complex)
