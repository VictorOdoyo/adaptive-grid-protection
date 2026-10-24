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
