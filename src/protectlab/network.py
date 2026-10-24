from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Branch:
    name: str
    start: str
    end: str
    z: object
    closed: bool = True

    def __post_init__(self):
        from .core import finite

        z = finite(self.z, ndim=2).copy()
        if z.shape != (3, 3) or np.linalg.matrix_rank(z) < 3 or not np.allclose(z, z.T):
            raise ValueError("reciprocal invertible 3x3 series impedance required")
        if np.linalg.eigvalsh(z.real).min() < -1e-12:
            raise ValueError("passive branch resistance required")
        if not self.name or not self.start or self.start == self.end:
            raise ValueError("named distinct branch endpoints required")
        z.setflags(write=False)
        object.__setattr__(self, "z", z)


@dataclass(frozen=True)
class Source:
    name: str
    bus: str
    emf: object
    z: object

    def __post_init__(self):
        from .core import finite

        emf = finite(self.emf).copy()
        checked = Branch(self.name, self.bus, self.bus + "__internal", self.z)
        if emf.shape != (3,):
            raise ValueError("three RMS source phase emfs required")
        emf.setflags(write=False)
        object.__setattr__(self, "emf", emf)
        object.__setattr__(self, "z", checked.z)


def balanced_source(name, bus, phase_voltage_v, z0, z1, z2=None, angle_rad=0):
    from .core import abc, phase_matrix, positive

    emf = abc([0, positive(phase_voltage_v) * np.exp(1j * angle_rad), 0])
    return Source(name, bus, emf, phase_matrix([z0, z1, z1 if z2 is None else z2]))


def admittance(buses, branches, sources=(), shunts=None):
    buses = tuple(buses)
    if not buses or len(set(buses)) != len(buses) or any(not isinstance(b, str) or not b for b in buses):
        raise ValueError("unique named buses required")
    indices = {bus: slice(3 * i, 3 * i + 3) for i, bus in enumerate(buses)}
    y = np.zeros((3 * len(buses),) * 2, complex)
    injection = np.zeros(3 * len(buses), complex)
    names = set()
    for branch in branches:
        if branch.name in names or branch.start not in indices or branch.end not in indices:
            raise ValueError("unique branch names and known endpoints required")
        names.add(branch.name)
        if not branch.closed:
            continue
        a, b = indices[branch.start], indices[branch.end]
        g = np.linalg.inv(branch.z)
        y[a, a] += g
        y[b, b] += g
        y[a, b] -= g
        y[b, a] -= g
    for source in sources:
        if source.bus not in indices:
            raise ValueError("source bus not found")
        s = indices[source.bus]
        g = np.linalg.inv(source.z)
        y[s, s] += g
        injection[s] += g @ source.emf
    for bus, shunt in (shunts or {}).items():
        from .core import finite

        g = finite(shunt)
        if bus not in indices or g.shape != (3, 3) or np.linalg.eigvalsh((g + g.conj().T) / 2).min() < -1e-12:
            raise ValueError("passive 3x3 shunt at known bus required")
        y[indices[bus], indices[bus]] += g
    return y, injection, indices


def solve(buses, branches, sources=(), shunts=None, injections=None, fault=None):
    y, j, indices = admittance(buses, branches, sources, shunts)
    for bus, current in (injections or {}).items():
        from .core import finite

        current = finite(current)
        if bus not in indices or current.shape != (3,):
            raise ValueError("three-phase injection at known bus required")
        j[indices[bus]] += current
    matrix, rhs = y, j
    if fault is not None:
        f = fault["connection"]
        resistance = fault["resistance_ohm"]
        if f.shape[1] != len(j):
            raise ValueError("fault connection does not match network")
        matrix = np.block([[y, f.T], [f, -np.eye(len(f)) * resistance]])
        rhs = np.r_[j, np.zeros(len(f))]
    try:
        solution = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError as error:
        raise ValueError("singular network: check grounding and energized connectivity") from error
    residual = float(np.linalg.norm(matrix @ solution - rhs) / max(np.linalg.norm(rhs), 1e-30))
    if not np.all(np.isfinite(solution)) or residual > 1e-8:
        raise RuntimeError("network solution did not satisfy KCL")
    voltage = solution[: len(j)]
    return {
        "voltage": {bus: voltage[s].copy() for bus, s in indices.items()},
        "fault_current": solution[len(j) :].copy(),
        "residual": residual,
    }


def fault_connection(buses, bus, kind="ag", resistance_ohm=0):
    from .core import positive

    buses = tuple(buses)
    if bus not in buses:
        raise ValueError("fault bus not found")
    patterns = {
        "ag": [[1, 0, 0]],
        "bg": [[0, 1, 0]],
        "cg": [[0, 0, 1]],
        "ab": [[1, -1, 0]],
        "bc": [[0, 1, -1]],
        "ca": [[-1, 0, 1]],
        "abg": [[1, 0, 0], [0, 1, 0]],
        "bcg": [[0, 1, 0], [0, 0, 1]],
        "cag": [[0, 0, 1], [1, 0, 0]],
        "abc": [[1, -1, 0], [0, 1, -1]],
        "abcg": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    }
    if kind not in patterns:
        raise ValueError("unknown fault kind")
    rows = np.asarray(patterns[kind], float)
    f = np.zeros((len(rows), 3 * len(buses)))
    index = buses.index(bus) * 3
    f[:, index : index + 3] = rows
    return {
        "connection": f,
        "resistance_ohm": positive(resistance_ohm, allow_zero=True),
        "bus": bus,
        "kind": kind,
    }


def currents(solution, branches, sources=()):
    voltage = solution["voltage"]
    branch_current = {
        b.name: (
            np.linalg.solve(b.z, voltage[b.start] - voltage[b.end]) if b.closed else np.zeros(3, complex)
        )
        for b in branches
    }
    source_current = {s.name: np.linalg.solve(s.z, s.emf - voltage[s.bus]) for s in sources}
    return {"branches": branch_current, "sources": source_current}


def power_balance(solution, branches, sources, shunts=None, injections=None, fault=None):
    from .core import power

    c = currents(solution, branches, sources)
    input_power = sum(power(solution["voltage"][s.bus], c["sources"][s.name]) for s in sources)
    input_power += sum(
        power(solution["voltage"][bus], current) for bus, current in (injections or {}).items()
    )
    line_loss = sum(np.vdot(c["branches"][b.name], b.z @ c["branches"][b.name]) for b in branches)
    # vdot computes I* Z I: complex absorbed line power.
    load = sum(
        power(solution["voltage"][bus], g @ solution["voltage"][bus]) for bus, g in (shunts or {}).items()
    )
    fault_loss = 0 if fault is None else fault["resistance_ohm"] * np.sum(abs(solution["fault_current"]) ** 2)
    return {
        "input_va": input_power,
        "line_va": line_loss,
        "load_va": load,
        "fault_w": fault_loss,
        "defect_va": input_power - line_loss - load - fault_loss,
    }
