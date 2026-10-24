import numpy as np


class Breaker:
    def __init__(self, opening_s=0.04, stuck=False):
        from .core import positive

        self.opening = positive(opening_s, allow_zero=True)
        self.stuck = bool(stuck)
        self.closed = True
        self.command_time = None
        self.open_time = None
        self.last_time = -np.inf

    def update(self, time_s, trip=False):
        if not np.isfinite(time_s) or time_s < self.last_time:
            raise ValueError("monotone finite breaker clock required")
        self.last_time = time_s
        if trip and self.command_time is None and self.closed:
            self.command_time = time_s
        if self.closed and self.command_time is not None and not self.stuck:
            if time_s - self.command_time >= self.opening - 1e-12:
                self.closed = False
                self.open_time = time_s
        return self.closed

    def close(self, time_s, permitted=False):
        if not permitted:
            return False
        if time_s < self.last_time or not np.isfinite(time_s):
            raise ValueError("monotone breaker close time required")
        self.closed = True
        self.command_time = None
        self.open_time = None
        self.last_time = time_s
        return True


class BreakerFailure:
    def __init__(self, delay_s=0.12, current_threshold_a=5):
        from .core import positive

        self.delay = positive(delay_s)
        self.threshold = positive(current_threshold_a)
        self.started = None
        self.tripped = False

    def update(self, time_s, trip_command, current_a, breaker_closed=True):
        from .core import positive

        current = positive(current_a, allow_zero=True)
        if not np.isfinite(time_s):
            raise ValueError("finite failure timer clock required")
        if trip_command and self.started is None:
            self.started = time_s
        if self.started is not None and time_s < self.started:
            raise ValueError("failure timer clock moved backwards")
        if not breaker_closed or current < self.threshold:
            self.started = None
        if self.started is not None and time_s - self.started >= self.delay - 1e-12:
            self.tripped = True
        return self.tripped


class ArcPole:
    def __init__(self, parting_s=0.03, zero_tolerance_a=0.01):
        from .core import positive

        self.parting = positive(parting_s, allow_zero=True)
        self.tolerance = positive(zero_tolerance_a, allow_zero=True)
        self.command = None
        self.closed = True
        self.previous = None

    def update(self, time_s, current_a, trip=False):
        if not np.all(np.isfinite([time_s, current_a])):
            raise ValueError("finite pole time and current required")
        if trip and self.command is None:
            self.command = time_s
        parted = self.command is not None and time_s - self.command >= self.parting - 1e-12
        crossing = self.previous is not None and self.previous * current_a <= 0
        if parted and (abs(current_a) <= self.tolerance or crossing):
            self.closed = False
        self.previous = current_a
        return self.closed


def sync_check(
    left_v,
    right_v,
    left_hz,
    right_hz,
    maximum_angle_rad=0.2,
    maximum_slip_hz=0.1,
    maximum_voltage_fraction=0.1,
    minimum_v=10,
):
    from .core import finite, positive

    left, right = complex(finite(left_v)), complex(finite(right_v))
    minimum = positive(minimum_v)
    if min(abs(left), abs(right)) < minimum:
        return False
    if not np.all(np.isfinite([left_hz, right_hz])):
        return False
    angle = abs(np.angle(left * np.conj(right)))
    mismatch = abs(abs(left) - abs(right)) / max(abs(left), abs(right))
    return bool(
        angle <= positive(maximum_angle_rad)
        and abs(left_hz - right_hz) <= positive(maximum_slip_hz)
        and mismatch <= positive(maximum_voltage_fraction)
    )


class Recloser:
    def __init__(self, dead_s=0.3, maximum_shots=1):
        from .core import integer, positive

        self.dead = positive(dead_s)
        self.maximum = integer(maximum_shots)
        self.shots = 0
        self.opened = None
        self.previous_closed = True
        self.locked = False

    def update(self, time_s, closed, permitted=False):
        if not np.isfinite(time_s):
            raise ValueError("finite recloser time required")
        if self.previous_closed and not closed:
            self.opened = time_s
            if self.shots >= self.maximum:
                self.locked = True
        self.previous_closed = bool(closed)
        ready = not closed and self.opened is not None and time_s - self.opened >= self.dead - 1e-12
        command = ready and permitted and not self.locked
        if command:
            self.shots += 1
            self.opened = None
        return bool(command)


def clearing_metrics(fault_s, pickup_s, trip_s, open_s):
    values = [fault_s, pickup_s, trip_s, open_s]
    known = [v for v in values if v is not None]
    if any(not np.isfinite(v) for v in known):
        raise ValueError("finite event timestamps required")
    if known != sorted(known):
        raise ValueError("event chronology is inconsistent")
    return {
        "detection_s": None if pickup_s is None else pickup_s - fault_s,
        "relay_s": None if trip_s is None else trip_s - fault_s,
        "breaker_s": None if trip_s is None or open_s is None else open_s - trip_s,
        "clearing_s": None if open_s is None else open_s - fault_s,
    }
