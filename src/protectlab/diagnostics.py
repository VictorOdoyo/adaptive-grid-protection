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
