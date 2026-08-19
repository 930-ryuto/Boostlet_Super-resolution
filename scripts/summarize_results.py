#!/usr/bin/env python3
"""Combine generated job CSVs and calculate condition-level summaries."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


GROUP_COLUMNS = [
    "Mask_Type",
    "Timing",
    "Method",
    "Boostlet_Level",
    "Sampling_Ratio",
    "Input_SNR",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("outputs/monte_carlo"))
    parser.add_argument("--output", type=Path, default=Path("outputs/summary"))
    args = parser.parse_args()
    files = sorted(args.input.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No result CSVs found in {args.input}")

    trials = pd.concat((pd.read_csv(path) for path in files), ignore_index=True)
    duplicate_keys = [
        "Mask_Type",
        "Timing",
        "Method",
        "Trial_ID",
        "Input_SNR",
        "Sampling_Ratio",
    ]
    if trials.duplicated(duplicate_keys).any():
        raise ValueError("Duplicate trial rows detected; check overlapping split outputs")

    grouped = trials.groupby(GROUP_COLUMNS, dropna=False)["RRMSE_Auto"]
    summary = grouped.agg(N="count", Mean="mean", SD="std", Median="median").reset_index()
    summary["SE"] = summary["SD"] / summary["N"] ** 0.5
    summary["CI95_Low"] = summary["Mean"] - 1.96 * summary["SE"]
    summary["CI95_High"] = summary["Mean"] + 1.96 * summary["SE"]

    args.output.mkdir(parents=True, exist_ok=True)
    trials.to_csv(args.output / "all_trials.csv", index=False)
    summary.to_csv(args.output / "rrmse_summary.csv", index=False)
    print(args.output / "rrmse_summary.csv")


if __name__ == "__main__":
    main()
