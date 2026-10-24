from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class Scenario:
    fault_kind: str = "abcg"
    fault_bus: str = "load"
    resistance_ohm: float = 0.2
    source_factor: float = 1.0
    inverter_current_a: float = 50.0
    inverter_limit_pu: float = 1.2
    negative_gain: float = 0.0
    duration_s: float = 0.8
    inception_s: float = 0.12
    removal_s: float | None = None
    sample_hz: int = 3200
    frequency_hz: float = 50.0
    opening_s: float = 0.04
    primary_stuck: bool = False
    adaptive: bool = False
    instrumented: bool = False
    ct_knee_vs: float = 0.4
    adc_scale_a: float = 20.0
    noise_a: float = 0.0
    dc_tau_s: float = 0.0
    seed: int = 42

    def __post_init__(self):
        from .core import integer, positive

        if self.fault_kind not in (
            "none",
            "ag",
            "bg",
            "cg",
            "ab",
            "bc",
            "ca",
            "abg",
            "bcg",
            "cag",
            "abc",
            "abcg",
        ):
            raise ValueError("unknown fault kind")
        if self.fault_bus not in ("load", "junction"):
            raise ValueError("fault bus must be load or junction")
        for name in (
            "source_factor",
            "duration_s",
            "frequency_hz",
            "ct_knee_vs",
            "adc_scale_a",
            "inverter_limit_pu",
        ):
            positive(getattr(self, name), name)
        for name in (
            "resistance_ohm",
            "inverter_current_a",
            "negative_gain",
            "opening_s",
            "noise_a",
            "dc_tau_s",
        ):
            positive(getattr(self, name), name, allow_zero=True)
        integer(self.sample_hz, 200)
        integer(self.seed, 0)
        if self.seed >= 2**32 or not 0 < self.inception_s < self.duration_s:
            raise ValueError("valid seed and fault inception inside capture required")
        if self.removal_s is not None and not self.inception_s < self.removal_s < self.duration_s:
            raise ValueError("fault removal must follow inception inside capture")
        cycle = self.sample_hz / self.frequency_hz
        if abs(cycle - round(cycle)) > 1e-9 or cycle < 8:
            raise ValueError("at least eight integer samples per nominal cycle required")
        if any(type(getattr(self, k)) is not bool for k in ("adaptive", "instrumented", "primary_stuck")):
            raise ValueError("scenario switches must be boolean")

    def to_dict(self):
        return asdict(self)


def feeder(scenario, primary_closed=True, backup_closed=True):
    from .core import phase_matrix
    from .inverters import Inverter
    from .network import Branch, balanced_source

    buses = ("source", "junction", "load")
    sources = [
        balanced_source(
            "grid",
            "source",
            11000 / np.sqrt(3),
            scenario.source_factor * (0.5 + 3j),
            scenario.source_factor * (0.3 + 1j),
        )
    ]
    branches = [
        Branch(
            "backup", "source", "junction", phase_matrix([0.5 + 1.5j, 0.2 + 0.6j, 0.2 + 0.6j]), backup_closed
        ),
        Branch(
            "primary", "junction", "load", phase_matrix([1.2 + 3.6j, 0.4 + 1.2j, 0.4 + 1.2j]), primary_closed
        ),
    ]
    shunts = {"load": np.eye(3) / 300}
    inverters = (
        []
        if scenario.inverter_current_a == 0
        else [
            Inverter(
                "pv",
                "load",
                scenario.inverter_current_a,
                11000 / np.sqrt(3),
                limit_pu=scenario.inverter_limit_pu,
                negative_gain=scenario.negative_gain,
            )
        ]
    )
    return {
        "buses": buses,
        "branches": branches,
        "sources": sources,
        "shunts": shunts,
        "inverters": inverters,
    }


def equilibrium(scenario, primary_closed=True, backup_closed=True, fault_active=False):
    from .inverters import solve_network
    from .network import currents, energized, fault_connection

    grid = feeder(scenario, primary_closed, backup_closed)
    active = energized(grid["buses"], grid["branches"], grid["sources"])
    buses = [b for b in grid["buses"] if b in active]
    branches = [b for b in grid["branches"] if b.start in active and b.end in active]
    fault = None
    if fault_active and scenario.fault_kind != "none" and scenario.fault_bus in active:
        fault = fault_connection(buses, scenario.fault_bus, scenario.fault_kind, scenario.resistance_ohm)
    result = solve_network(
        buses,
        branches,
        grid["sources"],
        [i for i in grid["inverters"] if i.bus in active],
        {b: y for b, y in grid["shunts"].items() if b in active},
        fault,
    )
    voltage = {b: np.zeros(3, complex) for b in grid["buses"]}
    voltage.update(result["voltage"])
    result["voltage"] = voltage
    result["branch_current"] = currents(result, grid["branches"])["branches"]
    result["deenergized"] = [b for b in grid["buses"] if b not in active]
    return result


def run(scenario):
    from .core import stream
    from .measurement import FourierWindow
    from .overcurrent import InverseRelay
    from .switchgear import Breaker

    time = np.arange(round(scenario.duration_s * scenario.sample_hz) + 1) / scenario.sample_hz
    dt = 1 / scenario.sample_hz
    n = len(time)
    relay = [InverseRelay(400, "very", 0.03), InverseRelay(450, "very", 0.12)]
    manager = setting_manager(scenario) if scenario.adaptive else None
    group_revision = np.ones(n, int)
    pickup_trace = np.zeros((n, 2))
    breakers = [Breaker(scenario.opening_s, scenario.primary_stuck), Breaker(scenario.opening_s)]
    if scenario.instrumented:
        from .frontend import CurrentFrontend
        from .instrument import CT

        model = CT(knee_vs=scenario.ct_knee_vs)
        windows = [
            CurrentFrontend(scenario.sample_hz, scenario.frequency_hz, model, scenario.adc_scale_a)
            for _ in range(2)
        ]
    else:
        windows = [FourierWindow(scenario.sample_hz, scenario.frequency_hz) for _ in range(2)]
    ct_flux = np.zeros((n, 2, 3))
    adc_clipped = np.zeros((n, 2, 3), bool)
    waves = np.zeros((n, 2, 3))
    true_current = np.zeros((n, 2, 3), complex)
    estimates = np.zeros((n, 2, 3), complex)
    valid = np.zeros((n, 2), bool)
    closed = np.ones((n, 2), bool)
    travel = np.zeros((n, 2))
    voltage = np.zeros((n, 3), complex)
    events = []
    cache = {}
    noise = stream(scenario.seed, "feeder-noise").normal(0, scenario.noise_a, (n, 2, 3))
    previous_closed = [True, True]
    dc_amplitude = np.zeros((2, 3))
    previous_fault = False
    actual_inception = None
    for k, t in enumerate(time):
        if manager is not None:
            from .adaptive import commit

            topology = f"source:{scenario.source_factor:g}"
            if commit(manager, t, topology, t, fault_active=any(r.picked for r in relay)):
                group = manager.active
                relay = [
                    InverseRelay(p, group.curve, tm)
                    for p, tm in zip(group.pickups_a, group.multipliers, strict=True)
                ]
                events.append({"time_s": float(t), "device": "settings", "event": "adaptive_commit"})
            group_revision[k] = manager.active.revision
        pickup_trace[k] = [r.pickup for r in relay]
        for b in breakers:
            b.update(t)
        state = (
            breakers[0].closed,
            breakers[1].closed,
            scenario.fault_kind != "none"
            and t >= scenario.inception_s
            and (scenario.removal_s is None or t < scenario.removal_s),
        )
        if state not in cache:
            cache[state] = equilibrium(scenario, *state[:2], fault_active=state[2])
        network = cache[state]
        if state[2] and not previous_fault:
            actual_inception = t
            if k and scenario.dc_tau_s > 0:
                for index, name in enumerate(("primary", "backup")):
                    dc_amplitude[index] = np.sqrt(2) * np.real(
                        (true_current[k - 1, index] - network["branch_current"][name])
                        * np.exp(2j * np.pi * scenario.frequency_hz * t)
                    )
        previous_fault = state[2]
        voltage[k] = network["voltage"]["junction"]
        for index, name in enumerate(("primary", "backup")):
            current = network["branch_current"][name]
            true_current[k, index] = current
            waves[k, index] = (
                np.sqrt(2) * np.real(current * np.exp(2j * np.pi * scenario.frequency_hz * t))
                + noise[k, index]
            )
            if (
                state[2]
                and actual_inception is not None
                and scenario.dc_tau_s > 0
                and state[index]
                and np.linalg.norm(current) > 1e-6
            ):
                waves[k, index] += dc_amplitude[index] * np.exp(-(t - actual_inception) / scenario.dc_tau_s)
            estimate = windows[index].update(t, waves[k, index])
            if scenario.instrumented:
                ct_flux[k, index] = [state.flux for state in windows[index].states]
                adc_clipped[k, index] = windows[index].clipped
            if estimate is not None:
                valid[k, index] = True
                estimates[k, index] = estimate
            before = relay[index].tripped
            if k:
                relay[index].update(
                    0 if estimate is None else float(np.max(abs(estimate))), dt, valid=estimate is not None
                )
            if relay[index].tripped and not before:
                events.append({"time_s": float(t), "device": name, "event": "trip"})
            breakers[index].update(t, relay[index].tripped)
            closed[k, index] = breakers[index].closed
            if previous_closed[index] and not breakers[index].closed:
                events.append({"time_s": float(t), "device": name, "event": "open"})
            previous_closed[index] = breakers[index].closed
            travel[k, index] = relay[index].travel
    fault_final = scenario.fault_kind != "none" and (
        scenario.removal_s is None or time[-1] < scenario.removal_s
    )
    final_state = (breakers[0].closed, breakers[1].closed, fault_final)
    if final_state not in cache:
        cache[final_state] = equilibrium(scenario, *final_state[:2], fault_active=final_state[2])
    return {
        "time_s": time,
        "group_revision": group_revision,
        "pickup_a": pickup_trace,
        "ct_flux_vs": ct_flux,
        "adc_clipped": adc_clipped,
        "current_wave_a": waves,
        "true_current_a": true_current,
        "phasor_a": estimates,
        "valid": valid,
        "breaker_closed": closed,
        "travel": travel,
        "voltage_v": voltage,
        "events": events,
        "final_voltage": cache[final_state]["voltage"],
        "maximum_network_residual": max(v["residual"] for v in cache.values()),
        "maximum_control_residual": max(v["control_residual"] for v in cache.values()),
    }


def setting_manager(scenario):
    from dataclasses import replace

    from .adaptive import Group, Manager, certify
    from .coordination import optimize

    def envelope(factor):
        rows = []
        for kind in ("ag", "bc", "abcg"):
            for resistance in (0.2, 2.0):
                condition = replace(
                    scenario,
                    source_factor=factor,
                    fault_kind=kind,
                    fault_bus="load",
                    resistance_ohm=resistance,
                )
                solved = equilibrium(condition, fault_active=True)
                rows.append(
                    [float(np.max(abs(solved["branch_current"][name]))) for name in ("primary", "backup")]
                )
        return np.asarray(rows)

    normal = envelope(1.0)
    base = Group("conventional", "source:1", 1, (400.0, 450.0), (0.03, 0.12))
    pairs = [(k, 0, 1) for k in range(len(normal))]
    manager = Manager(base, certify(base, normal, pairs), commit_delay_s=0.03)
    observed = envelope(scenario.source_factor)
    optimized = optimize(observed, [80, 100], pairs)
    group = Group(
        "adaptive", f"source:{scenario.source_factor:g}", 2, (80.0, 100.0), tuple(optimized["multipliers"])
    )
    certificate = certify(group, observed, pairs)
    manager.propose(group, certificate, group.topology, 0.0, 0.0)
    return manager
