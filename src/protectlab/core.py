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


def positive(value, name="parameter", allow_zero=False):
    if not np.isscalar(value) or np.iscomplexobj(value) or isinstance(value, (bool, np.bool_)):
        raise ValueError(name + " must be a finite real scalar")
    value = float(value)
    if not np.isfinite(value) or (value < 0 if allow_zero else value <= 0):
        raise ValueError(name + " must be positive" if not allow_zero else name + " must be nonnegative")
    return value


def integer(value, minimum=1):
    if type(value) is not int or value < minimum:
        raise ValueError("integer count required")
    return value
