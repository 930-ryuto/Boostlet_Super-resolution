# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared windows, masks, and noise realizations for paired comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np

from .config import ExperimentConfig


@dataclass(frozen=True)
class ScheduledCondition:
    trial_index: int
    trial_id: int
    t_start: int
    x_start: int
    snr_db: float
    standard_normal: np.ndarray


def iter_schedule(config: ExperimentConfig, timing: str) -> Iterator[ScheduledCondition]:
    """Yield the exact shared legacy RandomState stream in trial-then-SNR order."""
    timing = timing.lower()
    if timing not in config.time_ranges:
        raise ValueError(f"Unknown timing: {timing}")
    t_low, t_high = config.time_ranges[timing]
    x_low, x_high = config.x_start_range
    rng = np.random.RandomState(config.window_seed)
    t_starts = rng.randint(t_low, t_high + 1, config.trials)
    x_starts = rng.randint(x_low, max(x_low, x_high) + 1, config.trials)

    for trial_index in range(config.trials):
        for snr_db in config.input_snrs_db:
            yield ScheduledCondition(
                trial_index=trial_index,
                trial_id=trial_index + 1,
                t_start=int(t_starts[trial_index]),
                x_start=int(x_starts[trial_index]),
                snr_db=float(snr_db),
                standard_normal=rng.normal(0.0, 1.0, (config.nt, config.nx)),
            )


def make_mask(mask_type: str, sampling_ratio: float, nt: int, nx: int, trial_index: int) -> np.ndarray:
    """Create a trial-fixed random point mask or receiver-column mask."""
    rng = np.random.RandomState(trial_index)
    mask = np.zeros((nt, nx), dtype=float)
    if mask_type == "random":
        count = int(np.rint(sampling_ratio * nt * nx))
        mask.flat[rng.permutation(nt * nx)[:count]] = 1.0
    elif mask_type == "vertical":
        count = int(np.rint(sampling_ratio * nx))
        columns = rng.permutation(nx)[:count]
        mask[:, columns] = 1.0
    else:
        raise ValueError(f"Unknown mask type: {mask_type}")
    return mask


def make_calibration_mask(
    mask_type: str,
    sampling_ratio: float,
    nt: int,
    nx: int,
    seed: int,
) -> np.ndarray:
    rng = np.random.RandomState(seed)
    mask = np.zeros((nt, nx), dtype=float)
    if mask_type == "random":
        # The cutoff sweeps used truncation, while the Monte Carlo masks used
        # rounding. Keep that calibration convention explicit here.
        count = int(sampling_ratio * nt * nx)
        mask.flat[rng.permutation(nt * nx)[:count]] = 1.0
    elif mask_type == "vertical":
        count = int(np.rint(sampling_ratio * nx))
        columns = rng.permutation(nx)[:count]
        mask[:, columns] = 1.0
    else:
        raise ValueError(f"Unknown mask type: {mask_type}")
    return mask


def add_awgn(clean: np.ndarray, snr_db: float, standard_normal: np.ndarray) -> np.ndarray:
    if np.isinf(snr_db):
        return clean.copy()
    signal_power = float(np.mean(clean**2))
    noise_std = np.sqrt(signal_power / (10.0 ** (snr_db / 10.0)))
    return clean + noise_std * standard_normal
