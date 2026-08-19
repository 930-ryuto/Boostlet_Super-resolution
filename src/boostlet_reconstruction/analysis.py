# SPDX-License-Identifier: GPL-3.0-or-later
"""Paired statistical analysis of generated Monte Carlo results."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


CONDITION_COLUMNS = ["Mask_Type", "Timing", "Sampling_Ratio", "Input_SNR"]
PAIR_COLUMNS = CONDITION_COLUMNS + ["Trial_ID", "T_start", "X_start"]


def normalize_method_column(trials: pd.DataFrame) -> pd.DataFrame:
    """Accept both generated labels and the consolidated historical schema."""
    output = trials.copy()
    source_column = "Method_Label" if "Method_Label" in output.columns else "Method"
    if source_column not in output.columns:
        raise ValueError("Results require a Method or Method_Label column")

    normalized = output[source_column].astype(str).str.strip().str.lower()
    normalized = normalized.str.replace(" ", "_", regex=False)
    normalized = normalized.str.replace("boostlet_l=", "boostlet_l", regex=False)
    if "Boostlet_Level" in output.columns:
        plain_boostlet = normalized.eq("boostlet")
        levels = pd.to_numeric(output["Boostlet_Level"], errors="coerce")
        normalized.loc[plain_boostlet & levels.notna()] = (
            "boostlet_l" + levels.loc[plain_boostlet & levels.notna()].astype(int).astype(str)
        )
    output["Method"] = normalized
    return output


def holm_adjust(p_values: np.ndarray) -> np.ndarray:
    values = np.asarray(p_values, dtype=float)
    if values.ndim != 1:
        raise ValueError("p_values must be one-dimensional")
    count = len(values)
    order = np.argsort(values)
    adjusted = np.empty(count, dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        candidate = min(1.0, (count - rank) * values[index])
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted


def paired_against_shearlet(trials: pd.DataFrame) -> pd.DataFrame:
    required = set(PAIR_COLUMNS + ["Method", "RRMSE_Auto"])
    missing = required.difference(trials.columns)
    if missing:
        raise ValueError(f"Missing result columns: {sorted(missing)}")
    if trials.duplicated(PAIR_COLUMNS + ["Method"]).any():
        raise ValueError("Duplicate method rows prevent one-to-one pairing")

    wide = trials.pivot(index=PAIR_COLUMNS, columns="Method", values="RRMSE_Auto")
    if "shearlet" not in wide.columns:
        raise ValueError("Shearlet rows are required for paired comparisons")

    records: list[dict[str, float | int | str]] = []
    comparison_methods = sorted(method for method in wide.columns if method != "shearlet")
    for condition, group in wide.groupby(level=CONDITION_COLUMNS):
        for method in comparison_methods:
            paired = group[[method, "shearlet"]].dropna()
            if paired.empty:
                continue
            difference = paired[method].to_numpy() - paired["shearlet"].to_numpy()
            n = difference.size
            mean = float(np.mean(difference))
            sd = float(np.std(difference, ddof=1)) if n > 1 else np.nan
            se = sd / np.sqrt(n) if n > 1 else np.nan
            critical = float(stats.t.ppf(0.975, n - 1)) if n > 1 else np.nan
            test = stats.ttest_1samp(difference, popmean=0.0) if n > 1 else None
            record = dict(zip(CONDITION_COLUMNS, condition))
            record.update(
                {
                    "Comparison_Method": method,
                    "Reference_Method": "shearlet",
                    "N": n,
                    "Mean_Difference": mean,
                    "SD_Difference": sd,
                    "SE_Difference": se,
                    "CI95_Low": mean - critical * se if n > 1 else np.nan,
                    "CI95_High": mean + critical * se if n > 1 else np.nan,
                    "T_Statistic": float(test.statistic) if test is not None else np.nan,
                    "P_Raw": float(test.pvalue) if test is not None else np.nan,
                    "Win_Fraction": float(np.mean(difference < 0.0)),
                }
            )
            records.append(record)

    output = pd.DataFrame(records)
    if output.empty:
        return output
    output["P_Holm_Condition"] = output.groupby(CONDITION_COLUMNS, group_keys=False)[
        "P_Raw"
    ].transform(lambda values: holm_adjust(values.to_numpy()))
    output["P_Holm_Global"] = holm_adjust(output["P_Raw"].to_numpy())
    return output.sort_values(CONDITION_COLUMNS + ["Comparison_Method"]).reset_index(drop=True)


def method_rankings(trials: pd.DataFrame) -> pd.DataFrame:
    means = (
        trials.groupby(CONDITION_COLUMNS + ["Method"], as_index=False)["RRMSE_Auto"]
        .mean()
        .rename(columns={"RRMSE_Auto": "Mean_RRMSE"})
    )
    means["Rank"] = means.groupby(CONDITION_COLUMNS)["Mean_RRMSE"].rank(
        method="min", ascending=True
    )
    return means.sort_values(CONDITION_COLUMNS + ["Rank", "Method"]).reset_index(drop=True)


def best_boostlet_by_condition(trials: pd.DataFrame) -> pd.DataFrame:
    boostlet = trials[trials["Method"].str.startswith("boostlet_l")]
    means = boostlet.groupby(CONDITION_COLUMNS + ["Method"], as_index=False)[
        "RRMSE_Auto"
    ].mean()
    if means.empty:
        return means
    indices = means.groupby(CONDITION_COLUMNS)["RRMSE_Auto"].idxmin()
    output = means.loc[indices].rename(
        columns={"Method": "Best_Boostlet_Level", "RRMSE_Auto": "Mean_RRMSE"}
    )
    output["Selection_Status"] = "exploratory_condition_wise_selection"
    return output.sort_values(CONDITION_COLUMNS).reset_index(drop=True)


def write_analyses(trials_path: Path, output_directory: Path) -> list[Path]:
    trials = normalize_method_column(pd.read_csv(trials_path))
    output_directory.mkdir(parents=True, exist_ok=True)
    products = {
        "paired_vs_shearlet.csv": paired_against_shearlet(trials),
        "method_rankings.csv": method_rankings(trials),
        "best_boostlet_by_condition.csv": best_boostlet_by_condition(trials),
    }
    paths = []
    for name, frame in products.items():
        path = output_directory / name
        frame.to_csv(path, index=False)
        paths.append(path)
    return paths
