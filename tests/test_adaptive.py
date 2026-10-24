import numpy as np
import pytest

from protectlab import adaptive as m


def test_topology_fingerprint_ignores_list_order_but_detects_open_breaker():
    from dataclasses import replace

    from protectlab.network import Branch, balanced_source

    b = Branch("l", "a", "b", np.eye(3))
    s = balanced_source("g", "a", 230, 1j, 1j)
    original = m.topology_hash(["a", "b"], [b], [s])
    assert original == m.topology_hash(["b", "a"], [b], [s])
    assert original != m.topology_hash(["a", "b"], [replace(b, closed=False)], [s])


def test_setting_group_is_immutable_and_revision_changes_content_digest():
    from dataclasses import replace

    group = m.Group("normal", "hash", 1, (100, 100), (0.05, 0.2))
    assert group.digest() != replace(group, revision=2).digest()
    with pytest.raises(Exception):
        group.name = "tampered"


def test_coordination_certificate_cannot_be_reused_for_changed_pickup():
    from dataclasses import replace

    group = m.Group("normal", "hash", 1, (100, 100), (0.05, 0.2))
    certificate = m.certify(group, [[500, 500]], [(0, 0, 1)])
    assert m.verify_certificate(group, certificate)
    assert not m.verify_certificate(replace(group, pickups_a=(600, 100)), certificate)


def test_adaptive_proposal_rejects_stale_topology_and_rollback():
    from dataclasses import replace

    group = m.Group("base", "a", 1, (100, 100), (0.05, 0.2))
    certificate = m.certify(group, [[500, 500]], [(0, 0, 1)])
    manager = m.Manager(group, certificate)
    next_group = replace(group, name="weak", topology="b", revision=2)
    cert = m.certify(next_group, [[500, 500]], [(0, 0, 1)])
    with pytest.raises(ValueError, match="fresh"):
        manager.propose(next_group, cert, "b", 0, 1)
    with pytest.raises(ValueError, match="increasing"):
        manager.propose(group, certificate, "a", 0, 0)
