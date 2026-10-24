import pytest

from protectlab import events as m


def test_equal_time_events_keep_stable_order_and_reject_past_mutations():
    queue = m.Queue()
    queue.schedule(0.1, "fault")
    queue.schedule(0.1, "trip")
    assert [e["kind"] for e in queue.until(0.1)] == ["fault", "trip"]
    with pytest.raises(ValueError):
        queue.schedule(0.09, "late")
