# SPDX-License-Identifier: GPL-3.0-or-later
"""NBI line-array data loading and preprocessing."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import h5py
import numpy as np
from scipy.signal import resample_poly

from .config import DatasetConfig


@dataclass(frozen=True)
class WavefieldWindow:
    values: np.ndarray
    x_axis_m: np.ndarray
    sample_rate_hz: float


class NBILineDataset:
    """Read 1-D receiver windows using the preprocessing from the experiments."""

    def __init__(self, config: DatasetConfig):
        self.config = config

    def validate(self) -> None:
        path = self.config.path
        if not path.is_file():
            raise FileNotFoundError(
                f"Dataset not found: {path}. See data/README.md for the expected layout."
            )
        with h5py.File(path, "r") as handle:
            for key in (self.config.impulse_response_key, self.config.positions_key):
                if key not in handle:
                    raise KeyError(f"Dataset key not found in {path}: {key}")

    def load_window(self, nx: int, nt: int, x_start: int, t_start: int) -> WavefieldWindow:
        """Return a 1-based spatial/temporal window after propagation-rate resampling."""
        if min(nx, nt, x_start, t_start) < 1:
            raise ValueError("Window sizes and starts use positive, 1-based indexing")

        with h5py.File(self.config.path, "r") as handle:
            positions = np.asarray(handle[self.config.positions_key][0, :])
            impulse = handle[self.config.impulse_response_key]
            n_receivers = impulse.shape[0]
            if x_start + nx - 1 > n_receivers:
                raise ValueError(
                    f"Spatial window [{x_start}, {x_start + nx - 1}] exceeds "
                    f"the {n_receivers} receivers"
                )

            # The original code transposed the full array and reversed receiver order.
            # Reading only the needed receiver slab is equivalent and uses much less RAM.
            original_stop = n_receivers - (x_start - 1)
            original_start = original_stop - nx
            receiver_by_time = np.asarray(impulse[original_start:original_stop, :])

        x_axis = np.flipud(positions)
        selected_x = x_axis[x_start - 1 : x_start + nx - 1]
        dx = float(abs(x_axis[1] - x_axis[0]))
        target_rate = self.config.sound_speed_m_s / dx
        ratio = Fraction(target_rate / self.config.original_sample_rate_hz).limit_denominator(1_000_000)

        time_by_receiver = receiver_by_time[::-1, :].T
        resampled = resample_poly(time_by_receiver, ratio.numerator, ratio.denominator, axis=0)
        window = resampled[t_start - 1 : t_start + nt - 1, :]
        if window.shape != (nt, nx):
            raise ValueError(
                f"Temporal window [{t_start}, {t_start + nt - 1}] produced shape "
                f"{window.shape}, expected {(nt, nx)}"
            )
        return WavefieldWindow(np.asarray(window, dtype=float), selected_x, target_rate)
