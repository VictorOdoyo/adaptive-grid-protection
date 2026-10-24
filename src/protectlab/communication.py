import numpy as np


class Channel:
    def __init__(self, latency_s=0.005, jitter_s=0.0, loss_probability=0.0, seed=42):
        from .core import positive, stream
        from .events import Queue

        self.latency = positive(latency_s, allow_zero=True)
        self.jitter = positive(jitter_s, allow_zero=True)
        if not 0 <= loss_probability <= 1:
            raise ValueError("loss probability in [0,1] required")
        self.loss = loss_probability
        self.rng = stream(seed, "pilot-channel")
        self.queue = Queue()
        self.sequence = 0
        self.sent = 0
        self.dropped = 0

    def send(self, time_s, payload, sender="remote"):
        from copy import deepcopy

        if not np.isfinite(time_s) or time_s < self.queue.now:
            raise ValueError("finite causal send time required")
        self.sent += 1
        self.sequence += 1
        if self.rng.random() < self.loss:
            self.dropped += 1
            return False
        delay = max(0.0, self.latency + self.rng.uniform(-self.jitter, self.jitter))
        message = {
            "sent_s": float(time_s),
            "sequence": self.sequence,
            "sender": sender,
            "payload": deepcopy(payload),
        }
        self.queue.schedule(time_s + delay, "message", message)
        return True

    def receive(self, time_s):
        return [event["payload"] for event in self.queue.until(time_s)]


class Receiver:
    def __init__(self, sender="remote", maximum_age_s=0.02):
        from .core import positive

        self.sender = sender
        self.maximum_age = positive(maximum_age_s)
        self.sequence = 0
        self.message = None

    def accept(self, message, now_s):
        from copy import deepcopy

        try:
            age = now_s - message["sent_s"]
            valid = (
                message["sender"] == self.sender
                and type(message["sequence"]) is int
                and message["sequence"] > self.sequence
                and 0 <= age <= self.maximum_age
            )
        except (KeyError, TypeError):
            return False
        if not valid or not np.isfinite(age):
            return False
        self.sequence = message["sequence"]
        self.message = deepcopy(message)
        return True

    def latest(self, now_s):
        if self.message is None or not 0 <= now_s - self.message["sent_s"] <= self.maximum_age:
            return None
        return self.message["payload"].copy()


def permissive_trip(local_forward, local_pickup, remote_payload, channel_valid=True):
    remote = bool(channel_valid and isinstance(remote_payload, dict) and remote_payload.get("permit") is True)
    return bool(local_forward and local_pickup and remote)
