import numpy as np
import pytest

from protectlab import network as m


def test_branch_rejects_nonpassive_and_nonreciprocal_impedance():
    with pytest.raises(ValueError):
        m.Branch("x", "a", "b", -np.eye(3))
    line = m.Branch("line", "a", "b", np.eye(3) * (1 + 2j))
    with pytest.raises(ValueError):
        line.z[0, 0] = 3


def test_source_emf_and_impedance_keep_grounded_zero_sequence():
    from protectlab.core import seq

    source = m.balanced_source("grid", "a", 6350, 3j, 1j)
    assert seq(source.emf)[1] == pytest.approx(6350)
    assert np.allclose(source.z @ np.ones(3), np.ones(3) * 3j)
