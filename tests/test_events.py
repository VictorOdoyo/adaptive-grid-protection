import pytest

from protectlab import events as m


def test_equal_time_events_keep_stable_order_and_reject_past_mutations():
    queue = m.Queue()
    queue.schedule(0.1, "fault")
    queue.schedule(0.1, "trip")
    assert [e["kind"] for e in queue.until(0.1)] == ["fault", "trip"]
    with pytest.raises(ValueError):
        queue.schedule(0.09, "late")


def test_contact_chatter_does_not_commit_unstable_topology():
    d = m.Debounce(0.02)
    assert d.update(0, "a") is None
    assert d.update(0.01, "b") is None
    assert d.update(0.02, "a") is None
    assert d.update(0.03, "a") is None
    assert d.update(0.04, "a") == "a"
