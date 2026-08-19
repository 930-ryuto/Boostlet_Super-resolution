#!/usr/bin/env python3
"""Plot every fixed Boostlet level alongside the baseline methods."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ORDER = [
    "linear",
    "wavelet",
    "shearlet",
    "boostlet_l1",
    "boostlet_l2",
    "boostlet_l3",
    "boostlet_l4",
]
LABELS = {
    "linear": "Linear",
    "wavelet": "Wavelet",
    "shearlet": "Shearlet",
    "boostlet_l1": "Boostlet L1",
    "boostlet_l2": "Boostlet L2",
    "boostlet_l3": "Boostlet L3",
    "boostlet_l4": "Boostlet L4",
}
COLORS = {
    "linear": "#7f7f7f",
    "wavelet": "#9467bd",
    "shearlet": "#d62728",
    "boostlet_l1": "#17becf",
    "boostlet_l2": "#2ca02c",
    "boostlet_l3": "#1f77b4",
    "boostlet_l4": "#ff7f0e",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary", type=Path, default=Path("outputs/summary/rrmse_summary.csv")
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/figures"))
    args = parser.parse_args()
    frame = pd.read_csv(args.summary)
    args.output.mkdir(parents=True, exist_ok=True)

    for (mask_type, timing), subset in frame.groupby(["Mask_Type", "Timing"]):
        ratios = sorted(subset["Sampling_Ratio"].unique())
        figure, axes = plt.subplots(1, len(ratios), figsize=(4.2 * len(ratios), 3.7), sharey=True)
        if len(ratios) == 1:
            axes = [axes]
        for axis, ratio in zip(axes, ratios):
            ratio_data = subset[subset["Sampling_Ratio"] == ratio]
            for method in ORDER:
                method_data = ratio_data[ratio_data["Method"] == method].sort_values("Input_SNR")
                if method_data.empty:
                    continue
                axis.plot(
                    method_data["Input_SNR"],
                    method_data["Mean"],
                    marker="o",
                    linewidth=1.8,
                    markersize=4,
                    color=COLORS[method],
                    label=LABELS[method],
                )
                axis.fill_between(
                    method_data["Input_SNR"],
                    method_data["CI95_Low"],
                    method_data["CI95_High"],
                    color=COLORS[method],
                    alpha=0.10,
                    linewidth=0,
                )
            axis.set_title(rf"$\rho={ratio:.1f}$")
            axis.set_xlabel("Input SNR (dB)")
            axis.grid(alpha=0.25)
        axes[0].set_ylabel("RRMSE (%)")
        handles, labels = axes[-1].get_legend_handles_labels()
        figure.legend(handles, labels, loc="upper center", ncol=4, frameon=False)
        figure.suptitle(f"{mask_type.capitalize()} mask — {timing}", y=1.08)
        figure.tight_layout()
        stem = f"rrmse_{mask_type}_{str(timing).lower()}"
        figure.savefig(args.output / f"{stem}.pdf", bbox_inches="tight")
        figure.savefig(args.output / f"{stem}.png", dpi=220, bbox_inches="tight")
        plt.close(figure)


if __name__ == "__main__":
    main()
