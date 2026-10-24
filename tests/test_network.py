import numpy as np
import pytest

from protectlab import network as m


def test_branch_rejects_nonpassive_and_nonreciprocal_impedance():
    with pytest.raises(ValueError):
        m.Branch("x", "a", "b", -np.eye(3))
    line = m.Branch("line", "a", "b", np.eye(3) * (1 + 2j))
    with pytest.raises(ValueError):
        line.z[0, 0] = 3
