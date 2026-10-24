import numpy as np

from protectlab import adaptive as m


def test_topology_fingerprint_ignores_list_order_but_detects_open_breaker():
    from dataclasses import replace

    from protectlab.network import Branch, balanced_source

    b = Branch("l", "a", "b", np.eye(3))
    s = balanced_source("g", "a", 230, 1j, 1j)
    original = m.topology_hash(["a", "b"], [b], [s])
    assert original == m.topology_hash(["b", "a"], [b], [s])
    assert original != m.topology_hash(["a", "b"], [replace(b, closed=False)], [s])
