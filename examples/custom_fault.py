"""A custom single-line ground fault with independent engineering checks."""

import numpy as np

from protectlab.network import (
    balanced_source,
    currents,
    fault_connection,
    power_balance,
    sequence_reference,
    solve,
)


def calculate():
    source = balanced_source("grid", "bus", 6350, 3 + 8j, 1 + 3j)
    fault = fault_connection(["bus"], "bus", "ag", 1.0)
    solved = solve(["bus"], [], [source], fault=fault)
    phase = currents(solved, [], [source])["sources"]["grid"]
    reference = sequence_reference(6350, 3 + 8j, 1 + 3j, 1 + 3j, "ag", 1.0)["phase_a"]
    balance = power_balance(solved, [], [source], fault=fault)
    return {
        "current_a": phase,
        "relative_error": float(np.linalg.norm(phase - reference) / np.linalg.norm(reference)),
        "power_defect_va": complex(balance["defect_va"]),
    }


if __name__ == "__main__":
    result = calculate()
    print("Phase RMS current (A):", abs(result["current_a"]))
    print("Relative independent-reference error:", result["relative_error"])
    print("Complex-power defect (VA):", result["power_defect_va"])
