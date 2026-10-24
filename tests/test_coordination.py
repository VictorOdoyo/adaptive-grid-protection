import numpy as np

from protectlab import coordination as m


def test_coordination_audit_does_not_hide_unobservable_primary():
    r = m.audit([[500, 500], [80, 500]], [100, 100], [0.05, 0.2], [(0, 0, 1), (1, 0, 1)])
    assert r["rows"][0]["coordinated"]
    assert not r["rows"][1]["observable"]
    assert not r["coordinated"]


def test_tms_optimization_has_independently_audited_grading_margin():
    currents = np.array([[600, 500, 400], [800, 700, 600]])
    pairs = [(0, 0, 1), (0, 1, 2), (1, 0, 1), (1, 1, 2)]
    result = m.optimize(currents, [100, 100, 100], pairs)
    assert result["audit"]["coordinated"]
    assert np.all(result["multipliers"] >= 0.02 - 1e-12)
    assert min(row["margin_s"] for row in result["audit"]["rows"]) >= 0.2 - 1e-9


def test_low_inverter_fault_current_can_make_overcurrent_pickup_infeasible():
    assert m.pickup_interval(80, 1000)["feasible"]
    assert not m.pickup_interval(80, 96)["feasible"]


def test_robust_coordination_certifies_every_sample_not_only_nominal():
    samples = np.array([[[500, 450]], [[700, 400]], [[400, 550]]])
    result = m.robust_optimize(samples, [100, 100], [(0, 0, 1)])
    assert result["constraint_count"] == 3
    assert result["audit"]["coordinated"]
