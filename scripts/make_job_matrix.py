#!/usr/bin/env python3
"""Print reproducible calibration or Monte Carlo commands for local/HPC use."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
import shlex


def quote(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["calibration", "experiment"])
    parser.add_argument("--config", default="configs/paper.json")
    parser.add_argument("--calibration-config", default="configs/calibration.json")
    args = parser.parse_args()

    with Path(args.config).open(encoding="utf-8") as handle:
        config = json.load(handle)
    experiment = config["experiment"]

    if args.kind == "calibration":
        for mask_type, level, ratio in itertools.product(
            experiment["mask_types"], config["boostlet"]["levels"], experiment["sampling_ratios"]
        ):
            print(
                quote(
                    [
                        "python",
                        "scripts/run_calibration.py",
                        "--config",
                        args.config,
                        "--calibration-config",
                        args.calibration_config,
                        "--mask-type",
                        mask_type,
                        "--level",
                        str(level),
                        "--sampling-ratio",
                        str(ratio),
                    ]
                )
            )
    else:
        for method, mask_type, timing, ratio in itertools.product(
            experiment["methods"],
            experiment["mask_types"],
            experiment["timings"],
            experiment["sampling_ratios"],
        ):
            print(
                quote(
                    [
                        "python",
                        "scripts/run_experiment.py",
                        "--config",
                        args.config,
                        "--method",
                        method,
                        "--mask-type",
                        mask_type,
                        "--timing",
                        timing,
                        "--sampling-ratio",
                        str(ratio),
                    ]
                )
            )


if __name__ == "__main__":
    main()
