# SPDX-License-Identifier: GPL-3.0-or-later
"""Configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DatasetConfig:
    path: Path
    impulse_response_key: str
    positions_key: str
    original_sample_rate_hz: float
    sound_speed_m_s: float


@dataclass(frozen=True)
class ExperimentConfig:
    nx: int
    nt: int
    x_start_range: tuple[int, int]
    time_ranges: dict[str, tuple[int, int]]
    mask_types: tuple[str, ...]
    timings: tuple[str, ...]
    sampling_ratios: tuple[float, ...]
    input_snrs_db: tuple[float, ...]
    trials: int
    methods: tuple[str, ...]
    window_seed: int
    mask_seed_mode: str


@dataclass(frozen=True)
class SolverConfig:
    lambda_factors: tuple[float, ...]
    step_size: float
    max_iterations: int
    lcurve_smoothing: float
    lcurve_min_log_solution: float


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    dataset: DatasetConfig
    experiment: ExperimentConfig
    solver: SolverConfig
    linear: dict[str, Any]
    wavelet: dict[str, Any]
    shearlet: dict[str, Any]
    boostlet: dict[str, Any]
    output_directory: Path


def _required(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise ValueError(f"Missing required configuration key: {key}")
    return mapping[key]


def _resolve(project_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else project_root / path


def load_config(path: str | Path) -> AppConfig:
    """Load the main JSON configuration.

    Relative data/output paths are resolved from the repository root, defined as
    the parent of the ``configs`` directory containing the configuration file.
    """
    source = Path(path).expanduser().resolve()
    with source.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    project_root = source.parent.parent if source.parent.name == "configs" else source.parent
    d = _required(raw, "dataset")
    e = _required(raw, "experiment")
    s = _required(raw, "solver")

    dataset = DatasetConfig(
        path=_resolve(project_root, _required(d, "path")),
        impulse_response_key=_required(d, "impulse_response_key"),
        positions_key=_required(d, "positions_key"),
        original_sample_rate_hz=float(_required(d, "original_sample_rate_hz")),
        sound_speed_m_s=float(_required(d, "sound_speed_m_s")),
    )
    experiment = ExperimentConfig(
        nx=int(_required(e, "nx")),
        nt=int(_required(e, "nt")),
        x_start_range=tuple(map(int, _required(e, "x_start_range"))),
        time_ranges={k.lower(): tuple(map(int, v)) for k, v in _required(e, "time_ranges").items()},
        mask_types=tuple(str(v).lower() for v in _required(e, "mask_types")),
        timings=tuple(str(v).lower() for v in _required(e, "timings")),
        sampling_ratios=tuple(map(float, _required(e, "sampling_ratios"))),
        input_snrs_db=tuple(map(float, _required(e, "input_snrs_db"))),
        trials=int(_required(e, "trials")),
        methods=tuple(str(v).lower() for v in _required(e, "methods")),
        window_seed=int(_required(e, "window_seed")),
        mask_seed_mode=str(_required(e, "mask_seed_mode")),
    )
    solver = SolverConfig(
        lambda_factors=tuple(map(float, _required(s, "lambda_factors"))),
        step_size=float(_required(s, "step_size")),
        max_iterations=int(_required(s, "max_iterations")),
        lcurve_smoothing=float(_required(s, "lcurve_smoothing")),
        lcurve_min_log_solution=float(_required(s, "lcurve_min_log_solution")),
    )

    config = AppConfig(
        project_root=project_root,
        dataset=dataset,
        experiment=experiment,
        solver=solver,
        linear=dict(_required(raw, "linear")),
        wavelet=dict(_required(raw, "wavelet")),
        shearlet=dict(_required(raw, "shearlet")),
        boostlet=dict(_required(raw, "boostlet")),
        output_directory=_resolve(project_root, _required(raw, "output_directory")),
    )
    validate_config(config)
    return config


def validate_config(config: AppConfig) -> None:
    e = config.experiment
    if e.nx <= 0 or e.nt <= 0:
        raise ValueError("nx and nt must be positive")
    if e.trials <= 0:
        raise ValueError("trials must be positive")
    if e.mask_seed_mode != "trial_index":
        raise ValueError("Only mask_seed_mode='trial_index' reproduces the study")
    if any(mask not in {"random", "vertical"} for mask in e.mask_types):
        raise ValueError("mask_types must contain only 'random' and/or 'vertical'")
    if any(not 0.0 < ratio <= 1.0 for ratio in e.sampling_ratios):
        raise ValueError("sampling ratios must be in (0, 1]")
    if not config.solver.lambda_factors:
        raise ValueError("At least one lambda factor is required")
    if config.solver.step_size <= 0 or config.solver.max_iterations <= 0:
        raise ValueError("The FISTA step size and iteration count must be positive")


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).expanduser().open(encoding="utf-8") as handle:
        return json.load(handle)
