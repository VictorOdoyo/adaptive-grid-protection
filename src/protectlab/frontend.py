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
