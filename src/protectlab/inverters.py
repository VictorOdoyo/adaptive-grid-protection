import numpy as np


def priority_current(active, reactive, limit, priority="reactive"):
    from .core import positive

    limit = positive(limit)
    if not np.all(np.isfinite([active, reactive])) or priority not in ("reactive", "active"):
        raise ValueError("finite requests and active or reactive priority required")
    first, second = (reactive, active) if priority == "reactive" else (active, reactive)
    first = float(np.clip(first, -limit, limit))
    second = float(
        np.clip(second, -np.sqrt(max(0, limit**2 - first**2)), np.sqrt(max(0, limit**2 - first**2)))
    )
    return complex(second, -first) if priority == "reactive" else complex(first, -second)
