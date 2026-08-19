# SPDX-License-Identifier: GPL-3.0-or-later
"""Far-field cone projection used as the linear baseline."""

from __future__ import annotations

import numpy as np


def cone_interpolate(observed: np.ndarray, eta: float = 0.95) -> np.ndarray:
    nt, nx = observed.shape
    temporal_frequency = np.linspace(-1.0, 1.0, nt)[:, None]
    spatial_frequency = np.linspace(-1.0, 1.0, nx)[None, :]
    cone = (np.abs(spatial_frequency) < eta * np.abs(temporal_frequency)).astype(float)
    spectrum = np.fft.fftshift(np.fft.fft2(observed)) * cone
    return np.real(np.fft.ifft2(np.fft.ifftshift(spectrum)))
