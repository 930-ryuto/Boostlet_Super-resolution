# SPDX-License-Identifier: GPL-3.0-or-later
"""Adaptive Boostlet high-frequency cutoff tables."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .transforms.boostlet import BoostletDictionary


def cutoff_table_path(
    directory: Path, mask_type: str, level: int, sampling_ratio: float
) -> Path:
    ratio_percent = int(round(100.0 * sampling_ratio))
    return directory / f"boostlet_l{level}_{mask_type}_sr{ratio_percent}.csv"


def read_cutoff_table(path: Path) -> list[dict[str, float]]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Cutoff calibration table not found: {path}. Run boostlet-calibrate first."
        )
    rows: list[dict[str, float]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                {
                    "SNR": float(raw["SNR"]),
                    "Sampling_Ratio": float(raw["Sampling_Ratio"]),
                    "T_start": float(raw["T_start"]),
                    "Cutoff_Pct": float(raw["Cutoff_Pct"]),
                    "RRMSE": float(raw["RRMSE"]),
                }
            )
    if not rows:
        raise ValueError(f"Cutoff table is empty: {path}")
    return rows


def select_best_cutoff(
    rows: list[dict[str, float]],
    target_snr: float,
    target_sampling_ratio: float,
    target_t_start: int,
) -> float:
    """Select the best cutoff at each calibration time, then the nearest time."""
    filtered = [
        row
        for row in rows
        if np.isclose(row["SNR"], target_snr)
        and np.isclose(row["Sampling_Ratio"], target_sampling_ratio)
    ]
    if not filtered:
        raise ValueError(
            f"No cutoff calibration for SNR={target_snr}, "
            f"sampling_ratio={target_sampling_ratio}"
        )
    best_by_time: dict[int, dict[str, float]] = {}
    for row in filtered:
        t_start = int(row["T_start"])
        if t_start not in best_by_time or row["RRMSE"] < best_by_time[t_start]["RRMSE"]:
            best_by_time[t_start] = row
    nearest_time = min(best_by_time, key=lambda value: abs(value - target_t_start))
    return float(best_by_time[nearest_time]["Cutoff_Pct"])


def hybrid_removed_indices(
    dictionary: BoostletDictionary,
    cutoff_percent: float,
    fixed_indices: tuple[int, ...] | list[int],
) -> tuple[int, ...]:
    cutoff_indices = np.flatnonzero(dictionary.peak_radii > cutoff_percent / 100.0)
    return tuple(sorted(set(map(int, cutoff_indices)).union(map(int, fixed_indices))))
