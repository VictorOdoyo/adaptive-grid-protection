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
