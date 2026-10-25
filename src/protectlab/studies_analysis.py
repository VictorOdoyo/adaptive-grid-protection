import numpy as np


def fault_references(scale=1, seed=42):
    from .core import seq
    from .network import balanced_source, currents, fault_connection, sequence_reference, solve
    from .results import curve, make

    source = balanced_source("grid", "bus", 6350, 3 + 8j, 1 + 3j, 1.2 + 3.5j)
    rows = []
    all_phase = []
    for kind in ("ag", "bc", "bcg", "abcg"):
        result = solve(["bus"], [], [source], fault=fault_connection(["bus"], "bus", kind))
        current = currents(result, [], [source])["sources"]["grid"]
        expected = sequence_reference(6350, 3 + 8j, 1 + 3j, 1.2 + 3.5j, kind)["phase_a"]
        error = np.linalg.norm(current - expected) / np.linalg.norm(expected)
        components = seq(current)
        rows.append(
            {
                "kind": kind,
                "relative_error": float(error),
                "maximum_phase_a": float(max(abs(current))),
                "i0_a": float(abs(components[0])),
                "i1_a": float(abs(components[1])),
                "i2_a": float(abs(components[2])),
            }
        )
        all_phase.append(current)
    return make(
        "fault-reference-benchmarks",
        {"phase_emf_v": 6350, "z0_ohm": [3, 8], "z1_ohm": [1, 3], "z2_ohm": [1.2, 3.5], "seed": seed},
        {"maximum_relative_error": max(r["relative_error"] for r in rows)},
        {
            "case_index": np.arange(1, 5),
            "i0": [r["i0_a"] for r in rows],
            "i1": [r["i1_a"] for r in rows],
            "i2": [r["i2_a"] for r in rows],
            "phase_current_a": all_phase,
        },
        [
            curve(
                "Independent phase constraints and sequence references",
                "case_index",
                [("i0", "zero sequence"), ("i1", "positive sequence"), ("i2", "negative sequence")],
                "Fault: 1 AG, 2 BC, 3 BCG, 4 ABCG",
                "RMS sequence current (A)",
            )
        ],
        {"faults": rows},
        [
            "Bolted faults on a passive grounded conventional source.",
            "Unequal source positive and negative sequence impedances are retained.",
        ],
    )


def inverter_limits(scale=1, seed=42):
    from .core import abc, seq
    from .inverters import Inverter, requested_current
    from .results import curve, make

    voltage = np.linspace(0.02, 1.1, 101 * scale)
    reactive = Inverter("pv", "bus", 100, 230, negative_gain=0.8)
    active = Inverter("pv", "bus", 100, 230, negative_gain=0.8, priority="active")
    ir = np.array([requested_current(reactive, abc([0, 230 * v, 23 * np.exp(0.5j)])) for v in voltage])
    ia = np.array([requested_current(active, abc([0, 230 * v, 23 * np.exp(0.5j)])) for v in voltage])
    components = seq(ir)
    peaks = np.max(abs(ir), axis=1)
    return make(
        "inverter-current-ceilings",
        {
            "rated_current_a": 100,
            "phase_limit_a": 120,
            "negative_gain": 0.8,
            "negative_voltage_v": 23,
            "seed": seed,
        },
        {"maximum_phase_current_a": float(peaks.max()), "limit_excess_a": float(max(0, peaks.max() - 120))},
        {
            "voltage_pu": voltage,
            "reactive_priority": peaks,
            "active_priority": np.max(abs(ia), axis=1),
            "positive_reactive_a": -components[:, 1].imag,
            "negative_a": abs(components[:, 2]),
            "reactive_phase_a": ir,
            "active_phase_a": ia,
        },
        [
            curve(
                "Active/reactive priority with a phase-current ceiling",
                "voltage_pu",
                [("reactive_priority", "reactive priority"), ("active_priority", "active priority")],
                "Positive-sequence voltage (pu)",
                "Maximum phase RMS current (A)",
            ),
            curve(
                "Support allocation after the phase limiter",
                "voltage_pu",
                [("positive_reactive_a", "positive reactive current"), ("negative_a", "negative sequence")],
                "Positive-sequence voltage (pu)",
                "RMS current (A)",
            ),
        ],
        assumptions=[
            "Illustrative current-reference policy, not a manufacturer-specific inverter.",
            "The final limiter acts on the sum of sequence currents in phase coordinates.",
        ],
    )
