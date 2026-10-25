import pytest

from protectlab import communication as m


def test_channel_applies_latency_and_snapshots_payload():
    channel = m.Channel(0.01)
    payload = {"permit": True}
    channel.send(0, payload)
    payload["permit"] = False
    assert channel.receive(0.009) == []
    assert channel.receive(0.01)[0]["payload"]["permit"]
    lost = m.Channel(loss_probability=1)
    assert not lost.send(0, {})
    assert lost.receive(1) == []


def test_receiver_requires_fresh_monotonic_remote_message():
    receiver = m.Receiver()
    msg = {"sender": "remote", "sequence": 2, "sent_s": 0.1, "payload": {"permit": True}}
    assert receiver.accept(msg, 0.11)
    assert not receiver.accept(msg, 0.11)
    assert receiver.latest(0.121) is None
    assert not receiver.accept({**msg, "sender": "wrong", "sequence": 3}, 0.11)


def test_permissive_pilot_cannot_trip_on_remote_message_without_local_pickup():
    assert m.permissive_trip(True, True, {"permit": True})
    assert not m.permissive_trip(False, True, {"permit": True})
    assert not m.permissive_trip(True, False, {"permit": True})
    assert not m.permissive_trip(True, True, None)


def test_channel_metrics_separate_loss_from_delivered_latency():
    c = m.Channel(0.01)
    c.send(0, {})
    message = c.receive(0.02)[0]
    result = m.channel_metrics(c, [{**message, "received_s": 0.02}])
    assert result["delivery_fraction"] == 1
    assert result["maximum_delay_s"] == pytest.approx(0.02)


def test_received_nested_payload_cannot_mutate_saved_message():
    receiver = m.Receiver()
    message = {"sender": "remote", "sequence": 1, "sent_s": 0.0, "payload": {"limits": [1, 2]}}
    receiver.accept(message, 0.0)
    exposed = receiver.latest(0.0)
    exposed["limits"][0] = 99
    assert receiver.latest(0.0)["limits"][0] == 1


def test_transmitter_sequence_cannot_be_assigned_to_a_past_send_time():
    channel = m.Channel()
    channel.send(1.0, {})
    with pytest.raises(ValueError, match="causal"):
        channel.send(0.5, {})
