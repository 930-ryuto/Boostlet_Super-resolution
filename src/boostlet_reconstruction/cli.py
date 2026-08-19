# SPDX-License-Identifier: GPL-3.0-or-later
"""Command-line entry points."""

from __future__ import annotations

import argparse
from pathlib import Path

from .calibration import run_calibration
from .config import load_config, load_json
from .experiment import run_experiment


def experiment_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one paired Monte Carlo experiment job.")
    parser.add_argument("--config", default="configs/paper.json")
    parser.add_argument("--method", required=True)
    parser.add_argument("--mask-type", required=True, choices=["random", "vertical"])
    parser.add_argument("--timing", required=True, choices=["early", "late"])
    parser.add_argument("--sampling-ratio", required=True, type=float)
    parser.add_argument("--trial-start", type=int, default=1, help="First trial ID (1-based).")
    parser.add_argument("--trial-stop", type=int, help="Last trial ID (inclusive).")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def experiment_main(argv: list[str] | None = None) -> None:
    args = experiment_parser().parse_args(argv)
    config = load_config(args.config)
    stop = args.trial_stop or config.experiment.trials
    output = run_experiment(
        config=config,
        method=args.method,
        mask_type=args.mask_type,
        timing=args.timing,
        sampling_ratio=args.sampling_ratio,
        trial_start=args.trial_start - 1,
        trial_stop=stop,
        output_path=args.output,
        overwrite=args.overwrite,
    )
    print(output)


def calibration_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate one Boostlet cutoff table.")
    parser.add_argument("--config", default="configs/paper.json")
    parser.add_argument("--calibration-config", default="configs/calibration.json")
    parser.add_argument("--mask-type", required=True, choices=["random", "vertical"])
    parser.add_argument("--level", required=True, type=int, choices=[1, 2, 3, 4])
    parser.add_argument("--sampling-ratio", required=True, type=float)
    parser.add_argument("--snr", nargs="*", type=float)
    parser.add_argument("--t-start", nargs="*", type=int)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def calibration_main(argv: list[str] | None = None) -> None:
    args = calibration_parser().parse_args(argv)
    output = run_calibration(
        config=load_config(args.config),
        calibration_config=load_json(args.calibration_config),
        mask_type=args.mask_type,
        level=args.level,
        sampling_ratio=args.sampling_ratio,
        snrs=args.snr,
        t_starts=args.t_start,
        overwrite=args.overwrite,
    )
    print(output)
