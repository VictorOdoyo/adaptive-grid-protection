import numpy as np


def evaluate(scenario, name, expected_open, description):
    from .results import curve, make
    from .simulation import run

    capture = run(scenario)
    expected = set(expected_open)
    opened = {e["device"] for e in capture["events"] if e["event"] == "open"}
    correct = [e["time_s"] for e in capture["events"] if e["event"] == "open" and e["device"] in expected]
    measured = np.max(abs(capture["phasor_a"]), axis=2)
    actual = np.max(abs(capture["true_current_a"]), axis=2)
    nominal = 11000 / np.sqrt(3)
    voltage = np.max(abs(capture["voltage_v"]), axis=1) / nominal
    params = scenario.to_dict()
    params.update(
        {
            "line_positive_ohm": [[0.2, 0.6], [0.4, 1.2]],
            "line_zero_ohm": [[0.5, 1.5], [1.2, 3.6]],
            "load_resistance_ohm": 300,
            "line_voltage_v": 11000,
            "static_pickups_a": [400, 450],
            "static_time_multipliers": [0.03, 0.12],
            "adaptive_pickups_a": [80, 100],
            "grading_s": 0.2,
            "breaker_failure_delay_s": 0.12,
            "expected_open": list(expected_open),
            "certified_groups": capture["certified_groups"],
            "source_base_z1_ohm": [0.3, 1.0],
            "source_base_z0_ohm": [0.5, 3.0],
            "ct_ratio": 200.0,
            "ct_burden_ohm": 1.0,
            "ct_magnetizing_h": 20.0,
            "ct_saturated_h": 0.02,
            "adc_bits": 16,
            "analog_filter_order": 2,
            "analog_cutoff_hz": min(800.0, 0.4 * scenario.sample_hz),
            "directional_mta_rad": float(np.angle(0.4 + 1.2j)),
            "memory_hold_s": 0.6,
            "memory_minimum_v": 1000.0,
            "inverse_reset_s": 0.1,
            "inverse_dropout": 0.95,
        }
    )
    summary = {
        "selective": opened == expected,
        "required_isolation": bool(expected <= opened),
        "unnecessary_openings": len(opened - expected),
        "clearing_delay_s": None if not correct else min(correct) - scenario.inception_s,
        "primary_tripped": any(e["device"] == "primary" and e["event"] == "trip" for e in capture["events"]),
        "backup_tripped": any(e["device"] == "backup" and e["event"] == "trip" for e in capture["events"]),
        "maximum_primary_true_rms_a": float(np.max(actual[:, 0])),
        "primary_measurement_valid_fraction": float(np.mean(capture["valid"][:, 0])),
        "final_junction_voltage_pu": float(np.max(abs(capture["final_voltage"]["junction"])) / nominal),
        "maximum_network_residual": capture["maximum_network_residual"],
        "maximum_inverter_control_residual": capture["maximum_control_residual"],
    }
    arrays = {key: value for key, value in capture.items() if isinstance(value, np.ndarray)}
    arrays.update(
        {
            "primary_wave_a": capture["current_wave_a"][:, 0, 0],
            "primary_measured_a": measured[:, 0],
            "primary_true_a": actual[:, 0],
            "pickup_a": capture["pickup_a"][:, 0],
            "primary_valid": capture["valid"][:, 0],
            "primary_travel": capture["travel"][:, 0],
            "backup_travel": capture["travel"][:, 1],
            "junction_voltage_pu": voltage,
            "primary_closed": capture["breaker_closed"][:, 0].astype(float),
            "backup_closed": capture["breaker_closed"][:, 1].astype(float),
        }
    )
    return make(
        name,
        params,
        summary,
        arrays,
        [
            curve(
                "Primary phase-A waveform",
                "time_s",
                [("primary_wave_a", "sampled primary current")],
                "Time (s)",
                "Current (A)",
            ),
            curve(
                "Observed fundamental current and active pickup",
                "time_s",
                [
                    ("primary_measured_a", "measured RMS", "primary_valid"),
                    ("primary_true_a", "true maximum phase RMS"),
                    ("pickup_a", "active pickup"),
                ],
                "Time (s)",
                "Current (A)",
            ),
            curve(
                "Integrated inverse-time travel",
                "time_s",
                [("primary_travel", "primary"), ("backup_travel", "backup")],
                "Time (s)",
                "Normalized travel",
            ),
            curve(
                "Voltage and interruption feedback",
                "time_s",
                [
                    ("junction_voltage_pu", "junction maximum phase voltage (pu)"),
                    ("primary_closed", "primary closed = 1"),
                    ("backup_closed", "backup closed = 1"),
                ],
                "Time (s)",
                "Per unit / binary state",
            ),
        ],
        {"events": capture["events"]},
        [
            description,
            "This is a quasi-steady phase-network and sampled-waveform feedback model, not a full switching EMT solver.",
            "GFL inverter islands without a voltage-forming reference are deenergized after isolation.",
            "RMS phasors use a fixed cosine reference. Relay decisions use measured signals, not fault truth.",
            "The supplied expected breaker set is used only to score the completed replay.",
            "The CT is a piecewise-linear excitation model without hysteresis; DC offsets are synthesized per fault segment.",
        ],
    )


def strong(scale=1, seed=42):
    from .simulation import Scenario

    return evaluate(
        Scenario(sample_hz=3200 * scale, seed=seed),
        "strong-source",
        ["primary"],
        "Conventional settings protect the downstream zone with a strong conventional source.",
    )


def weak_static(scale=1, seed=42):
    from .simulation import Scenario

    return evaluate(
        Scenario(source_factor=20, sample_hz=3200 * scale, seed=seed),
        "weak-source-static",
        ["primary"],
        "Conventional 400 A pickup is intentionally retained after source strength decreases.",
    )


def weak_adaptive(scale=1, seed=42):
    from .simulation import Scenario

    return evaluate(
        Scenario(source_factor=20, adaptive=True, sample_hz=3200 * scale, seed=seed),
        "weak-source-adaptive",
        ["primary"],
        "A certified 80/100 A group is committed before fault inception, with a modeled 0.2 s grading margin.",
    )


def earth(scale=1, seed=42):
    from .simulation import Scenario

    return evaluate(
        Scenario(fault_kind="ag", source_factor=20, adaptive=True, sample_hz=3200 * scale, seed=seed),
        "earth-fault-adaptive",
        ["primary"],
        "The single-line-to-ground case retains zero-sequence source and line impedances.",
    )


def phase_fault(scale=1, seed=42):
    from .simulation import Scenario

    return evaluate(
        Scenario(fault_kind="bc", source_factor=20, adaptive=True, sample_hz=3200 * scale, seed=seed),
        "phase-fault-adaptive",
        ["primary"],
        "Line-to-line faults have no direct ground connection and cannot rely on residual-current pickup.",
    )


def instrumented(scale=1, seed=42):
    from .simulation import Scenario

    return evaluate(
        Scenario(instrumented=True, adc_scale_a=40.0, dc_tau_s=0.04, sample_hz=3200 * scale, seed=seed),
        "instrumented-fault",
        ["primary"],
        "Nonlinear CT, causal low-pass, 16-bit ADC and full-cycle estimation precede both relays.",
    )


def saturation(scale=1, seed=42):
    from .simulation import Scenario

    return evaluate(
        Scenario(instrumented=True, ct_knee_vs=0.025, dc_tau_s=0.06, sample_hz=3200 * scale, seed=seed),
        "ct-saturation",
        ["primary"],
        "A low illustrative CT flux knee deliberately stresses measured current; the model is not a CT accuracy class.",
    )


def clipping(scale=1, seed=42):
    from .simulation import Scenario

    return evaluate(
        Scenario(instrumented=True, adc_scale_a=0.05, sample_hz=3200 * scale, seed=seed),
        "adc-clipping",
        ["primary"],
        "The ADC rail is intentionally too small. Invalid windows are blocked and the missed operation is retained.",
    )


def breaker_failure(scale=1, seed=42):
    from .simulation import Scenario

    return evaluate(
        Scenario(primary_stuck=True, sample_hz=3200 * scale, seed=seed),
        "breaker-failure",
        ["backup"],
        "The primary trip is latched but its breaker is stuck. Persistent measured current starts 50BF backup.",
    )


def reverse_infeed(scale=1, seed=42):
    from .simulation import Scenario

    return evaluate(
        Scenario(fault_bus="junction", inverter_current_a=1000, sample_hz=3200 * scale, seed=seed),
        "directional-challenge",
        ["backup"],
        "High inverter export is an intentional stress case. Conventional memory torque may classify reverse fault current as forward.",
    )


def healthy(scale=1, seed=42):
    from .simulation import Scenario

    return evaluate(
        Scenario(fault_kind="none", inverter_current_a=300, sample_hz=3200 * scale, seed=seed),
        "healthy-export",
        [],
        "A fault-free export case measures relay security under reverse normal current.",
    )


def temporary(scale=1, seed=42):
    from .simulation import Scenario

    return evaluate(
        Scenario(removal_s=0.14, sample_hz=3200 * scale, seed=seed),
        "temporary-fault",
        [],
        "The imposed fault is removed after 20 ms. Relay travel must decay without an unnecessary delayed trip.",
    )
