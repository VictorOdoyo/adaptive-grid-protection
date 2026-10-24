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
