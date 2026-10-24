import numpy as np


class Queue:
    def __init__(self):
        self.heap = []
        self.counter = 0
        self.now = -np.inf

    def schedule(self, time_s, kind, payload=None):
        import heapq

        if not np.isfinite(time_s) or time_s < self.now or not isinstance(kind, str):
            raise ValueError("future finite event time and named kind required")
        heapq.heappush(self.heap, (float(time_s), self.counter, kind, payload))
        self.counter += 1

    def until(self, time_s):
        import heapq

        if not np.isfinite(time_s) or time_s < self.now:
            raise ValueError("monotone event clock required")
        self.now = time_s
        events = []
        while self.heap and self.heap[0][0] <= time_s + 1e-12:
            when, sequence, kind, payload = heapq.heappop(self.heap)
            events.append({"time_s": when, "sequence": sequence, "kind": kind, "payload": payload})
        return events


class Debounce:
    def __init__(self, duration_s=0.02):
        from .core import positive

        self.duration = positive(duration_s)
        self.candidate = None
        self.started = None
        self.value = None

    def update(self, time_s, value):
        if not np.isfinite(time_s):
            raise ValueError("finite topology sample time required")
        if value != self.candidate:
            self.candidate = value
            self.started = time_s
        if time_s - self.started >= self.duration - 1e-12:
            self.value = self.candidate
        return self.value
