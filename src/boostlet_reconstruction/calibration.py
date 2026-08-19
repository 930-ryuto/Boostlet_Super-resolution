# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate the Boostlet cutoff sweep tables used by the main experiments."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import numpy as np

from .config import AppConfig
from .cutoff import cutoff_table_path
from .data import NBILineDataset
from .sampling import add_awgn, make_calibration_mask
from .solvers import sweep_lambdas
from .transforms.boostlet import (
    BoostletOperator,
    build_boostlet_dictionary,
    parseval_error,
)


CALIBRATION_FIELDS = [
    "Mask_Type",
    "Boostlet_Level",
    "SNR",
    "Sampling_Ratio",
    "T_start",
    "X_start",
    "Cutoff_Pct",
    "Atoms",
    "Parseval_Err",
    "Lambda_Oracle",
    "RRMSE",
]


def run_calibration(
    config: AppConfig,
    calibration_config: dict,
    mask_type: str,
    level: int,
    sampling_ratio: float,
    snrs: Iterable[float] | None = None,
    t_starts: Iterable[int] | None = None,
    overwrite: bool = False,
) -> Path:
    e = config.experiment
    if e.nx != e.nt:
        raise ValueError("Boostlet calibration requires nx == nt")
    if level not in {1, 2, 3, 4}:
        raise ValueError("level must be one of 1, 2, 3, 4")
    mask_type = mask_type.lower()
    snr_values = list(map(float, snrs or calibration_config["snrs_db"]))
    time_values = list(map(int, t_starts or calibration_config["t_starts"]))
    cutoff_values = list(
        map(float, calibration_config["cutoff_percentages"][str(level)])
    )
    x_start = int(calibration_config["x_start"])
    output_directory = Path(calibration_config["output_directory"])
    if not output_directory.is_absolute():
        output_directory = config.project_root / output_directory
    destination = cutoff_table_path(output_directory, mask_type, level, sampling_ratio)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Calibration output already exists: {destination}. Use --overwrite to replace it."
        )

    dataset = NBILineDataset(config.dataset)
    dataset.validate()
    full_dictionary = build_boostlet_dictionary(
        size=e.nx,
        level_count=level,
        h0=float(config.boostlet["h0"]),
        alpha=float(config.boostlet["alpha"]),
        use_top_cap=bool(config.boostlet["use_top_cap"]),
    )
    standard_normal = np.random.RandomState(
        int(calibration_config["noise_seed"])
    ).normal(0.0, 1.0, (e.nt, e.nx))

    rows: list[dict[str, float | int | str]] = []
    for t_start in time_values:
        reference = dataset.load_window(e.nx, e.nt, x_start, t_start).values
        mask = make_calibration_mask(
            mask_type,
            sampling_ratio,
            e.nt,
            e.nx,
            int(calibration_config["mask_seed_offset"]) + t_start,
        )
        for snr_db in snr_values:
            noisy = add_awgn(reference, snr_db, standard_normal)
            for cutoff_percent in cutoff_values:
                dictionary = full_dictionary.subset_by_cutoff(cutoff_percent / 100.0)
                operator = BoostletOperator(dictionary)
                sweep = sweep_lambdas(noisy, mask, reference, operator, config.solver)
                rows.append(
                    {
                        "Mask_Type": mask_type,
                        "Boostlet_Level": level,
                        "SNR": snr_db,
                        "Sampling_Ratio": sampling_ratio,
                        "T_start": t_start,
                        "X_start": x_start,
                        "Cutoff_Pct": cutoff_percent,
                        "Atoms": dictionary.atom_count,
                        "Parseval_Err": parseval_error(dictionary),
                        "Lambda_Oracle": sweep.oracle_lambda,
                        "RRMSE": sweep.oracle_metrics["RRMSE"],
                    }
                )

    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CALIBRATION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return destination
