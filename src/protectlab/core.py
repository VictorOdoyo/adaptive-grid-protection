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


A = np.exp(2j * np.pi / 3)
SEQUENCE = np.array([[1, 1, 1], [1, A**2, A], [1, A, A**2]], complex)


def abc(sequence):
    value = finite(sequence)
    if value.shape[-1] != 3:
        raise ValueError("final axis must have three components")
    return value @ SEQUENCE.T


def seq(phases):
    value = finite(phases)
    if value.shape[-1] != 3:
        raise ValueError("final axis must have three phases")
    return value @ np.linalg.inv(SEQUENCE).T


def phase_matrix(sequence_impedances):
    values = finite(sequence_impedances)
    if values.shape != (3,):
        raise ValueError("three sequence impedances required")
    return SEQUENCE @ np.diag(values) @ np.linalg.inv(SEQUENCE)


def power(voltage, current):
    v, i = np.broadcast_arrays(finite(voltage), finite(current))
    if v.shape[-1] != 3:
        raise ValueError("three-phase final axis required")
    return np.sum(v * np.conj(i), axis=-1)


def bases(power_va, line_voltage_v):
    s, v = positive(power_va), positive(line_voltage_v)
    return {
        "power_va": s,
        "line_voltage_v": v,
        "phase_voltage_v": v / np.sqrt(3),
        "current_a": s / (np.sqrt(3) * v),
        "impedance_ohm": v * v / s,
    }
