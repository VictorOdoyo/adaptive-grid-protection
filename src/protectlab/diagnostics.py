import numpy as np


def two_ended(left_v, right_v, left_i, right_i, line_z, minimum_current_a=1.0):
    from .core import finite, positive

    vl, vr, il, ir = [finite(x) for x in (left_v, right_v, left_i, right_i)]
    z = finite(line_z, ndim=2)
    if any(x.shape != (3,) for x in (vl, vr, il, ir)) or z.shape != (3, 3):
        raise ValueError("three-phase terminals and full line impedance required")
    predictor = z @ (il + ir)
    response = vl - vr + z @ ir
    observed = np.linalg.norm(il + ir) >= positive(minimum_current_a)
    denominator = float(np.vdot(predictor, predictor).real)
    if not observed or denominator <= 1e-20:
        return {"valid": False, "fraction": None, "residual_v": None}
    location = float(np.vdot(predictor, response).real / denominator)
    residual = float(np.linalg.norm(response - location * predictor))
    return {"valid": bool(0 <= location <= 1), "fraction": location, "residual_v": residual}


def reactance_location(apparent_ohm, line_ohm, minimum_reactance=0.001):
    from .core import finite, positive

    z = finite(apparent_ohm)
    line = complex(finite(line_ohm))
    if abs(line.imag) < positive(minimum_reactance):
        raise ValueError("observable line reactance required")
    fraction = z.imag / line.imag
    return {"fraction": fraction, "valid": (fraction >= 0) & (fraction <= 1)}


def takagi(voltage, current, prefault_current, line_ohm, minimum_denominator=1e-6):
    from .core import finite, positive

    v, i, pre = [complex(finite(x)) for x in (voltage, current, prefault_current)]
    increment = i - pre
    denominator = float(np.imag(line_ohm * i * np.conj(increment)))
    if abs(denominator) < positive(minimum_denominator):
        return {"fraction": None, "valid": False}
    value = float(np.imag(v * np.conj(increment)) / denominator)
    return {"fraction": value, "valid": bool(0 <= value <= 1)}


def signature(voltage, current, prefault_voltage, prefault_current, minimum_a=1.0):
    from .core import finite, positive, seq

    v, i = finite(voltage), finite(current)
    dv, di = seq(v - finite(prefault_voltage)), seq(i - finite(prefault_current))
    if v.shape != (3,) or i.shape != (3,):
        raise ValueError("one set of terminal phase values required")
    observable = np.linalg.norm(di) >= positive(minimum_a)
    total = float(np.linalg.norm(di))
    return {
        "observable": bool(observable),
        "delta_i0_a": float(abs(di[0])),
        "delta_i1_a": float(abs(di[1])),
        "delta_i2_a": float(abs(di[2])),
        "zero_fraction": 0.0 if not observable else float(abs(di[0]) / total),
        "negative_fraction": 0.0 if not observable else float(abs(di[2]) / total),
        "delta_v_sequence": dv,
    }


def arrival_location(left_time_s, right_time_s, length_m, velocity_m_s, maximum_skew_s=0.0):
    from .core import positive

    length, velocity = positive(length_m), positive(velocity_m_s)
    skew = positive(maximum_skew_s, allow_zero=True)
    if not np.all(np.isfinite([left_time_s, right_time_s])):
        raise ValueError("finite arrival timestamps required")
    position = (length + velocity * (left_time_s - right_time_s)) / 2
    return {
        "position_m": position,
        "valid": bool(0 <= position <= length),
        "clock_error_bound_m": velocity * skew / 2,
    }


def unbalance(voltage, current, minimum_v=1.0, minimum_a=0.1):
    from .core import positive, seq

    v, i = seq(voltage), seq(current)
    valid = abs(v[..., 1]) >= positive(minimum_v)
    ratio = np.divide(abs(v[..., 2]), abs(v[..., 1]), out=np.zeros_like(abs(v[..., 1])), where=valid)
    return {
        "voltage_negative_ratio": ratio,
        "voltage_valid": valid,
        "negative_current_observable": abs(i[..., 2]) >= positive(minimum_a),
    }


def fit_frequency(time, values, bounds_hz=(45.0, 55.0), harmonics=(1, 2), dc=True):
    from scipy.optimize import minimize_scalar

    from .core import finite, timebase
    from .measurement import least_squares

    t = timebase(time)
    v = finite(values, real=True)
    lower, upper = bounds_hz
    if not 0 < lower < upper or not np.all(np.isfinite(bounds_hz)):
        raise ValueError("positive ordered frequency search bounds required")

    def objective(frequency):
        return least_squares(t, v, frequency, harmonics, dc)["residual"] ** 2

    fit = minimize_scalar(objective, bounds=bounds_hz, method="bounded", options={"xatol": 1e-10})
    if not fit.success:
        raise RuntimeError("frequency fit failed")
    estimate = least_squares(t, v, fit.x, harmonics, dc)
    return {**estimate, "frequency_hz": float(fit.x)}
