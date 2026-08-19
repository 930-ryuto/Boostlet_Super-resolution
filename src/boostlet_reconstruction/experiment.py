# SPDX-License-Identifier: GPL-3.0-or-later
"""Unified Monte Carlo runner for all methods and mask types."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np

from .config import AppConfig
from .cutoff import (
    cutoff_table_path,
    hybrid_removed_indices,
    read_cutoff_table,
    select_best_cutoff,
)
from .data import NBILineDataset
from .metrics import reconstruction_metrics
from .sampling import add_awgn, iter_schedule, make_mask
from .solvers import sweep_lambdas
from .transforms.boostlet import BoostletOperator, build_boostlet_dictionary
from .transforms.linear import cone_interpolate
from .transforms.shearlet import ShearletOperator
from .transforms.wavelet import WaveletOperator


RESULT_FIELDS = [
    "Mask_Type",
    "Timing",
    "Method",
    "Boostlet_Level",
    "Trial_ID",
    "Input_SNR",
    "Sampling_Ratio",
    "T_start",
    "X_start",
    "Cutoff_Pct",
    "Hybrid_Removed_Atoms",
    "Lambda_Auto",
    "Lambda_Oracle",
    "RRMSE_Auto",
    "RRMSE_Oracle",
    "OutputSNR_Auto",
    "PSNR_Auto",
    "SSIM_Auto",
    "SolNorm_Auto",
    "ResNorm_Auto",
]


def parse_boostlet_level(method: str) -> int | None:
    prefix = "boostlet_l"
    if not method.startswith(prefix):
        return None
    try:
        level = int(method[len(prefix) :])
    except ValueError as exc:
        raise ValueError(f"Invalid Boostlet method name: {method}") from exc
    if level not in {1, 2, 3, 4}:
        raise ValueError(f"Boostlet level must be L1--L4, got {level}")
    return level


def default_output_path(
    config: AppConfig,
    method: str,
    mask_type: str,
    timing: str,
    sampling_ratio: float,
    trial_start: int,
    trial_stop: int,
) -> Path:
    ratio = int(round(100.0 * sampling_ratio))
    name = (
        f"{method}_{mask_type}_{timing}_sr{ratio}_"
        f"trials{trial_start + 1}-{trial_stop}.csv"
    )
    return config.output_directory / name


def _base_row(
    method: str,
    level: int | None,
    mask_type: str,
    timing: str,
    sampling_ratio: float,
    condition: Any,
) -> dict[str, Any]:
    return {
        "Mask_Type": mask_type,
        "Timing": timing.capitalize(),
        "Method": method,
        "Boostlet_Level": level,
        "Trial_ID": condition.trial_id,
        "Input_SNR": condition.snr_db,
        "Sampling_Ratio": sampling_ratio,
        "T_start": condition.t_start,
        "X_start": condition.x_start,
        "Cutoff_Pct": None,
        "Hybrid_Removed_Atoms": None,
        "Lambda_Auto": None,
        "Lambda_Oracle": None,
        "RRMSE_Auto": None,
        "RRMSE_Oracle": None,
        "OutputSNR_Auto": None,
        "PSNR_Auto": None,
        "SSIM_Auto": None,
        "SolNorm_Auto": None,
        "ResNorm_Auto": None,
    }


def _write_rows(path: Path, rows: list[dict[str, Any]], overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {path}. Use --overwrite to replace it.")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(
    config: AppConfig,
    method: str,
    mask_type: str,
    timing: str,
    sampling_ratio: float,
    trial_start: int = 0,
    trial_stop: int | None = None,
    output_path: Path | None = None,
    overwrite: bool = False,
) -> Path:
    """Run one method/mask/timing/ratio job with shared trials and noise."""
    method = method.lower()
    mask_type = mask_type.lower()
    timing = timing.lower()
    e = config.experiment
    trial_stop = e.trials if trial_stop is None else trial_stop
    if method not in e.methods:
        raise ValueError(f"Method is not enabled in the configuration: {method}")
    if mask_type not in e.mask_types:
        raise ValueError(f"Mask type is not enabled in the configuration: {mask_type}")
    if timing not in e.timings:
        raise ValueError(f"Timing is not enabled in the configuration: {timing}")
    if not any(np.isclose(sampling_ratio, value) for value in e.sampling_ratios):
        raise ValueError(f"Sampling ratio is not enabled: {sampling_ratio}")
    if not 0 <= trial_start < trial_stop <= e.trials:
        raise ValueError(f"Trial slice must satisfy 0 <= start < stop <= {e.trials}")

    dataset = NBILineDataset(config.dataset)
    dataset.validate()
    level = parse_boostlet_level(method)
    fixed_operator: Any = None
    boostlet_dictionary = None
    cutoff_rows = None

    if method == "wavelet":
        fixed_operator = WaveletOperator(
            (e.nt, e.nx),
            name=str(config.wavelet["name"]),
            level=int(config.wavelet["level"]),
            mode=str(config.wavelet["mode"]),
        )
    elif method == "shearlet":
        fixed_operator = ShearletOperator(
            (e.nt, e.nx),
            scales=int(config.shearlet["scales"]),
            removed_indices=config.shearlet["removed_indices"],
        )
    elif level is not None:
        if e.nx != e.nt:
            raise ValueError("The Boostlet implementation requires nx == nt")
        boostlet_dictionary = build_boostlet_dictionary(
            size=e.nx,
            level_count=level,
            h0=float(config.boostlet["h0"]),
            alpha=float(config.boostlet["alpha"]),
            use_top_cap=bool(config.boostlet["use_top_cap"]),
        )
        if bool(config.boostlet.get("use_adaptive_cutoff", True)):
            cutoff_directory = Path(config.boostlet["cutoff_tables"])
            if not cutoff_directory.is_absolute():
                cutoff_directory = config.project_root / cutoff_directory
            cutoff_rows = read_cutoff_table(
                cutoff_table_path(cutoff_directory, mask_type, level, sampling_ratio)
            )
    elif method != "linear":
        raise ValueError(f"Unknown method: {method}")

    rows: list[dict[str, Any]] = []
    current_trial = -1
    reference = None
    for condition in iter_schedule(e, timing):
        if not trial_start <= condition.trial_index < trial_stop:
            continue
        if condition.trial_index != current_trial:
            reference = dataset.load_window(
                e.nx, e.nt, condition.x_start, condition.t_start
            ).values
            current_trial = condition.trial_index
        assert reference is not None
        noisy = add_awgn(reference, condition.snr_db, condition.standard_normal)
        mask = make_mask(mask_type, sampling_ratio, e.nt, e.nx, condition.trial_index)
        row = _base_row(
            method, level, mask_type, timing, sampling_ratio, condition
        )

        if method == "linear":
            reconstruction = cone_interpolate(
                noisy * mask, eta=float(config.linear["cone_eta"])
            )
            metrics = reconstruction_metrics(reference, reconstruction)
            row.update(
                {
                    "RRMSE_Auto": metrics["RRMSE"],
                    "RRMSE_Oracle": metrics["RRMSE"],
                    "OutputSNR_Auto": metrics["Output_SNR"],
                    "PSNR_Auto": metrics["PSNR"],
                    "SSIM_Auto": metrics["SSIM"],
                }
            )
        else:
            operator = fixed_operator
            if level is not None:
                assert boostlet_dictionary is not None
                fixed_indices = config.boostlet["fixed_removed_indices"][str(level)]
                if cutoff_rows is not None:
                    cutoff_percent = select_best_cutoff(
                        cutoff_rows,
                        condition.snr_db,
                        sampling_ratio,
                        condition.t_start,
                    )
                    removed = hybrid_removed_indices(
                        boostlet_dictionary, cutoff_percent, fixed_indices
                    )
                    row["Cutoff_Pct"] = cutoff_percent
                else:
                    removed = tuple(map(int, fixed_indices))
                row["Hybrid_Removed_Atoms"] = len(removed)
                operator = BoostletOperator(boostlet_dictionary, removed)

            sweep = sweep_lambdas(noisy, mask, reference, operator, config.solver)
            row.update(
                {
                    "Lambda_Auto": sweep.auto_lambda,
                    "Lambda_Oracle": sweep.oracle_lambda,
                    "RRMSE_Auto": sweep.auto_metrics["RRMSE"],
                    "RRMSE_Oracle": sweep.oracle_metrics["RRMSE"],
                    "OutputSNR_Auto": sweep.auto_metrics["Output_SNR"],
                    "PSNR_Auto": sweep.auto_metrics["PSNR"],
                    "SSIM_Auto": sweep.auto_metrics["SSIM"],
                    "SolNorm_Auto": sweep.auto_solution_log10,
                    "ResNorm_Auto": sweep.auto_residual_log10,
                }
            )
        rows.append(row)

    destination = output_path or default_output_path(
        config, method, mask_type, timing, sampling_ratio, trial_start, trial_stop
    )
    _write_rows(destination, rows, overwrite)
    return destination
