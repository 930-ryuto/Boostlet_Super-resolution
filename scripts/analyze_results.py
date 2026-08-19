#!/usr/bin/env python3
"""Run paired tests, rankings, and exploratory best-level analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

from boostlet_reconstruction.analysis import write_analyses


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--trials", type=Path, default=Path("outputs/summary/all_trials.csv")
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/analysis"))
    args = parser.parse_args()
    for path in write_analyses(args.trials, args.output):
        print(path)


if __name__ == "__main__":
    main()
