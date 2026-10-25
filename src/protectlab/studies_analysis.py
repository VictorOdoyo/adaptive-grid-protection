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


def negative_sequence(scale=1, seed=42):
    from .core import abc, seq
    from .directional import negative_sequence as direction
    from .inverters import Inverter, requested_current
    from .results import curve, make

    gains = np.linspace(0, 1, 51 * scale)
    voltage = abc([0, 115, 23 * np.exp(0.4j)])
    rows = []
    for gain in gains:
        model = Inverter("pv", "bus", 100, 230, negative_gain=float(gain))
        current = requested_current(model, voltage)
        operating = direction(voltage, current, minimum_current_a=1)
        rows.append(
            {
                "gain": float(gain),
                "negative_a": float(abs(seq(current)[2])),
                "observable": bool(operating["valid"]),
                "forward": bool(operating["forward"]),
            }
        )
    return make(
        "negative-sequence-observability",
        {
            "positive_voltage_v": 115,
            "negative_voltage_v": 23,
            "negative_angle_rad": 0.4,
            "minimum_operating_current_a": 1,
            "seed": seed,
        },
        {"zero_gain_observable": rows[0]["observable"], "full_gain_current_a": rows[-1]["negative_a"]},
        {
            "gain": gains,
            "negative_a": [r["negative_a"] for r in rows],
            "observable": [float(r["observable"]) for r in rows],
        },
        [
            curve(
                "Negative-sequence availability depends on inverter control",
                "gain",
                [("negative_a", "negative-sequence RMS")],
                "Negative current gain",
                "RMS current (A)",
            ),
            curve(
                "Directional-element observability",
                "gain",
                [("observable", "valid = 1")],
                "Negative current gain",
                "Binary validity",
            ),
        ],
        {"sweep": rows},
        [
            "Voltage unbalance alone does not guarantee negative-sequence operating current.",
            "The torque direction shown belongs to this explicit current-reference policy.",
        ],
    )


def dc_rejection(scale=1, seed=42):
    from .measurement import dft, mimic
    from .results import curve, make
    from .waveforms import rl_fault

    fs = 3200 * scale
    t = np.arange(round(0.2 * fs) + 1) / fs
    current = rl_fault(t, 1, 0.03, 230, angle_rad=0.2)
    raw = dft(t, current)
    filtered = mimic(current, fs, 0.03)
    corrected = dft(t, filtered["values"], quality=filtered["valid"])
    expected = 230 * np.exp(0.2j) / (1 + 2j * np.pi * 50 * 0.03)
    filtered_phasor = corrected["phasor"] / filtered["response"]
    valid = corrected["valid"]
    raw_error = abs(raw["phasor"] - expected) / abs(expected)
    corrected_error = abs(filtered_phasor - expected) / abs(expected)
    return make(
        "dc-offset-rejection",
        {
            "resistance_ohm": 1,
            "inductance_h": 0.03,
            "voltage_rms_v": 230,
            "frequency_hz": 50,
            "inception_angle_rad": 0.2,
            "sample_hz": fs,
            "seed": seed,
        },
        {
            "maximum_valid_raw_error": float(raw_error[valid].max()),
            "maximum_valid_mimic_error": float(corrected_error[valid].max()),
        },
        {
            "time_s": t,
            "current_a": current,
            "raw_error": raw_error,
            "mimic_error": corrected_error,
            "valid": valid,
            "raw_phasor_a": raw["phasor"],
            "mimic_phasor_a": filtered_phasor,
        },
        [
            curve(
                "Independent RL current with decaying offset",
                "time_s",
                [("current_a", "fault current")],
                "Time (s)",
                "Instantaneous current (A)",
            ),
            curve(
                "Complex fundamental error includes phase",
                "time_s",
                [("raw_error", "full-cycle Fourier"), ("mimic_error", "mimic with phase correction")],
                "Time (s)",
                "Relative complex error",
                valid="valid",
            ),
        ],
        assumptions=[
            "Mimic cancellation assumes the stated RL decay constant.",
            "Its known complex frequency response is removed before phasor comparison.",
        ],
    )


def off_nominal(scale=1, seed=42):
    from .diagnostics import fit_frequency
    from .measurement import dft
    from .results import curve, make
    from .waveforms import synthesize

    fs = 3200 * scale
    t = np.arange(round(0.12 * fs) + 1) / fs
    expected = np.array([100 + 20j, -40 - 90j, -60 + 70j])
    waveform = synthesize(t, expected, 48.7) + 3
    fixed = dft(t, waveform, 50)
    fit = fit_frequency(t, waveform)
    reference = expected[None, :] * np.exp(2j * np.pi * (48.7 - 50) * t[:, None])
    error = np.linalg.norm(fixed["phasor"] - reference, axis=1) / np.linalg.norm(expected)
    recovered = np.asarray(fit["phasors"][1])
    return make(
        "off-nominal-estimation",
        {
            "actual_frequency_hz": 48.7,
            "nominal_frequency_hz": 50,
            "dc_offset_a": 3,
            "sample_hz": fs,
            "fit_bounds_hz": [45, 55],
            "seed": seed,
        },
        {
            "estimated_frequency_hz": fit["frequency_hz"],
            "frequency_error_hz": abs(fit["frequency_hz"] - 48.7),
            "fitted_phasor_relative_error": float(
                np.linalg.norm(recovered - expected) / np.linalg.norm(expected)
            ),
        },
        {
            "time_s": t,
            "fixed_error": error,
            "valid": fixed["valid"],
            "wave_a": waveform[:, 0],
            "phasor_reference": reference,
            "fitted_phasor": recovered,
        },
        [
            curve(
                "Off-nominal waveform with unknown DC",
                "time_s",
                [("wave_a", "phase A")],
                "Time (s)",
                "Current (A)",
            ),
            curve(
                "Nominal full-cycle leakage against rotating reference",
                "time_s",
                [("fixed_error", "relative complex error")],
                "Time (s)",
                "Relative error",
                valid="valid",
            ),
        ],
        assumptions=[
            "Frequency is estimated by bounded variable projection with joint DC and harmonic fitting.",
            "This offline fit is not a claimed causal real-time frequency tracker.",
        ],
    )


def ct_burden(scale=1, seed=42):
    from .instrument import CT, simulate
    from .results import curve, make
    from .waveforms import rl_fault

    fs = 6400 * scale
    t = np.arange(round(0.16 * fs) + 1) / fs
    primary = rl_fault(t, 0.2, 0.01, 6000)
    captures = [simulate(t, primary, CT(burden_ohm=r, knee_vs=0.04)) for r in (0.2, 1.0, 3.0)]
    fractions = [float(np.mean(c["saturated"])) for c in captures]
    arrays = {"time_s": t, "ideal_secondary_a": primary / 200, "primary_a": primary}
    for k, capture in enumerate(captures):
        arrays[f"secondary_{k}"] = capture["secondary_a"]
        arrays[f"flux_{k}"] = capture["flux_vs"]
    return make(
        "ct-burden-sensitivity",
        {
            "primary_source_rms_v": 6000,
            "primary_resistance_ohm": 0.2,
            "primary_inductance_h": 0.01,
            "ratio": 200,
            "knee_vs": 0.04,
            "burdens_ohm": [0.2, 1, 3],
            "sample_hz": fs,
            "seed": seed,
        },
        {"low_burden_saturated_fraction": fractions[0], "high_burden_saturated_fraction": fractions[-1]},
        arrays,
        [
            curve(
                "Burden changes secondary distortion",
                "time_s",
                [
                    ("ideal_secondary_a", "ideal ratio"),
                    ("secondary_0", "0.2 ohm"),
                    ("secondary_1", "1 ohm"),
                    ("secondary_2", "3 ohm"),
                ],
                "Time (s)",
                "Secondary current (A)",
            ),
            curve(
                "Flux-linkage state retained for each burden",
                "time_s",
                [("flux_0", "0.2 ohm"), ("flux_1", "1 ohm"), ("flux_2", "3 ohm")],
                "Time (s)",
                "Secondary flux linkage (V s)",
            ),
        ],
        {
            "burdens": [
                {"burden_ohm": r, "saturated_fraction": f}
                for r, f in zip((0.2, 1, 3), fractions, strict=True)
            ]
        },
        ["Piecewise-linear magnetization without hysteresis or a manufacturer CT accuracy-class claim."],
    )


def coordination(scale=1, seed=42):
    from .coordination import optimize
    from .overcurrent import operating_time
    from .results import curve, make

    currents = np.array([[600, 500, 400], [900, 700, 550], [1200, 1000, 800]])
    pairs = [(f, p, p + 1) for f in range(3) for p in range(2)]
    optimized = optimize(currents, [100, 120, 150], pairs)
    sweep = np.linspace(160, 1500, 201 * scale)
    settings = optimized["multipliers"]
    arrays = {"current_a": sweep}
    for k, pickup in enumerate((100, 120, 150)):
        arrays[f"time_{k}"] = operating_time(sweep / pickup, "very") * settings[k]
    margins = [r["margin_s"] for r in optimized["audit"]["rows"]]
    return make(
        "coordination-optimization",
        {
            "fault_currents_a": currents,
            "pickups_a": [100, 120, 150],
            "grading_s": 0.2,
            "breaker_s": 0.04,
            "seed": seed,
        },
        {"minimum_margin_s": min(margins), "objective_sum_tms": optimized["objective"]},
        arrays,
        [
            curve(
                "Optimized relay time curves; constraints use each relay's local fault current",
                "current_a",
                [(f"time_{k}", f"relay {k + 1}") for k in range(3)],
                "Local RMS current (A)",
                "Relay operating time (s)",
                "log",
                "log",
            )
        ],
        {
            "settings": [
                {"relay": k, "pickup_a": p, "time_multiplier": float(settings[k])}
                for k, p in enumerate((100, 120, 150))
            ],
            "margins": optimized["audit"]["rows"],
        },
        [
            "Curve separation at equal current is illustrative; grading is certified at the distinct local currents in the fault matrix."
        ],
    )


def robust_coordination(scale=1, seed=42):
    from .coordination import audit, optimize, robust_optimize
    from .core import stream
    from .results import curve, make

    rng = stream(seed, "coordination-envelope")
    nominal = np.array([[500.0, 450.0], [700.0, 600.0]])
    samples = np.maximum(150, nominal[None, :, :] * (1 + rng.normal(0, 0.12, (40 * scale, 2, 2))))
    pairs = [(0, 0, 1), (1, 0, 1)]
    conventional = optimize(nominal, [100, 100], pairs)
    robust = robust_optimize(samples, [100, 100], pairs)
    nominal_margins = []
    robust_margins = []
    for sample in samples:
        nominal_margins.append(
            min(r["margin_s"] for r in audit(sample, [100, 100], conventional["multipliers"], pairs)["rows"])
        )
        robust_margins.append(
            min(r["margin_s"] for r in audit(sample, [100, 100], robust["multipliers"], pairs)["rows"])
        )
    return make(
        "robust-coordination",
        {
            "nominal_currents_a": nominal,
            "relative_std": 0.12,
            "sample_count": len(samples),
            "pickups_a": [100, 100],
            "grading_s": 0.2,
            "seed": seed,
        },
        {
            "nominal_settings_worst_margin_s": min(nominal_margins),
            "robust_settings_worst_margin_s": min(robust_margins),
        },
        {
            "sample": np.arange(1, len(samples) + 1),
            "nominal_margin": nominal_margins,
            "robust_margin": robust_margins,
            "current_samples_a": samples,
        },
        [
            curve(
                "Worst primary-backup margin for each sampled condition",
                "sample",
                [
                    ("nominal_margin", "nominal optimization"),
                    ("robust_margin", "sample-envelope optimization"),
                ],
                "Fault-current sample",
                "Grading margin (s)",
            )
        ],
        assumptions=[
            "Samples are an assumed stress envelope, not measured grid uncertainty.",
            "Robust feasibility is established only for the supplied samples, not all possible faults.",
        ],
    )
