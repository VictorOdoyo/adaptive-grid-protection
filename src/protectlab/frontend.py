import numpy as np


class Frontend:
    def __init__(self, sample_hz=3200, frequency_hz=50, cutoff_hz=800):
        from scipy.signal import butter

        from .core import positive
        from .measurement import FourierWindow

        self.fs = positive(sample_hz)
        cutoff = positive(cutoff_hz)
        if cutoff >= self.fs / 2:
            raise ValueError("frontend cutoff below Nyquist required")
        self.sos = butter(2, cutoff, fs=self.fs, output="sos")
        self.zi = np.zeros((len(self.sos), 2, 3))
        self.window = FourierWindow(self.fs, frequency_hz)
        self.filtered = np.zeros(3)

    def update(self, time_s, values, valid=True):
        from scipy.signal import sosfilt

        from .core import finite

        value = finite(values, real=True)
        if value.shape != (3,):
            raise ValueError("three real measurement channels required")
        filtered, self.zi = sosfilt(self.sos, value[None, :], axis=0, zi=self.zi)
        self.filtered = filtered[0]
        return self.window.update(time_s, self.filtered, valid)


class CurrentFrontend:
    def __init__(
        self, sample_hz=3200, frequency_hz=50, ct=None, full_scale_a=20.0, bits=16, initial_flux_vs=0.0
    ):
        from .core import positive
        from .instrument import CT, CTState

        self.model = CT() if ct is None else ct
        self.states = [CTState(self.model, initial_flux_vs) for _ in range(3)]
        self.filter = Frontend(sample_hz, frequency_hz, min(800.0, 0.4 * sample_hz))
        self.rail = positive(full_scale_a)
        self.bits = bits
        self.secondary = np.zeros(3)
        self.clipped = np.zeros(3, bool)

    def update(self, time_s, primary_a, valid=True):
        from .core import finite
        from .measurement import adc

        current = finite(primary_a, real=True)
        if current.shape != (3,):
            raise ValueError("three current channels required")
        self.secondary = np.array(
            [state.update(time_s, value) for state, value in zip(self.states, current, strict=True)]
        )
        result = adc(self.secondary, self.rail, self.bits)
        self.clipped = result["clipped"]
        estimate = self.filter.update(time_s, result["values"], valid and not np.any(self.clipped))
        return None if estimate is None else estimate * self.model.ratio
