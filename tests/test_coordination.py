from protectlab import coordination as m


def test_coordination_audit_does_not_hide_unobservable_primary():
    r = m.audit([[500, 500], [80, 500]], [100, 100], [0.05, 0.2], [(0, 0, 1), (1, 0, 1)])
    assert r["rows"][0]["coordinated"]
    assert not r["rows"][1]["observable"]
    assert not r["coordinated"]
