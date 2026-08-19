# Validation record

Validation date: 2026-08-19

This record describes checks performed while consolidating the research scripts
into the public repository. Generated verification artifacts were kept outside
the repository.

## Static and packaging checks

- All Python files compiled successfully.
- All JSON configuration files parsed successfully.
- The source distribution built as a Python wheel.
- The wheel contained both project GPL-3.0 license text and the vendored
  pyShearLab license/copyright notices.
- The public-release audit found no credential pattern, personal absolute path,
  file larger than 50 MB, input HDF5 file, or generated result file.
- The Git staged-diff whitespace check passed.

## Unit tests

Fifteen tests passed. They cover:

- paper configuration values;
- deterministic windows, masks, and AWGN;
- Boostlet construction, cutoff, transform shapes, and coefficient masking;
- Linear reconstruction;
- L-curve fallback behavior;
- cutoff-table selection;
- Holm adjustment;
- vendored pyShearLab execution with NumPy 2;
- public-release safety.

## NBI loader equivalence

For a 32-by-32 window at `X_start=52`, `T_start=606`, the optimized slab reader
was compared with the historical implementation that loaded, transposed, and
reversed the complete HDF5 array. All values matched exactly (`rtol=0`,
`atol=0`).

## Boostlet dictionary equivalence

The consolidated dictionaries were compared with the selected historical
hybrid builder at size 128. Filters agreed to numerical roundoff (`rtol=1e-15`,
`atol=1e-15`), and peak-radius arrays matched exactly.

| Level | Number of atoms |
|---|---:|
| L1 | 41 |
| L2 | 63 |
| L3 | 77 |
| L4 | 87 |

## End-to-end smoke run

One real HDF5 window was reconstructed successfully with each method family:

- Linear;
- Wavelet;
- Shearlet;
- Boostlet L1.

The smoke configuration used a 32-by-32 window, one SNR, one lambda, and two
FISTA iterations. All four outputs used identical trial ID, window coordinates,
mask, and noise schedule. A reduced L1 cutoff calibration, CSV aggregation, and
PDF/PNG figure generation also completed successfully.

## Statistical validation against consolidated results

The analysis code was run read-only against the existing 42,000-row consolidated
trial table. It produced:

- 360 paired comparisons against Shearlet;
- 420 condition/method ranking rows;
- 60 exploratory best-Boostlet rows.

The following counts matched the existing research summary exactly:

| Mask | Level | Mean-RRMSE wins vs Shearlet | Wins after condition-wise Holm correction |
|---|---|---:|---:|
| random | L1 | 0 | 0 |
| random | L2 | 23 | 20 |
| random | L3 | 24 | 21 |
| random | L4 | 15 | 13 |
| vertical | L1 | 0 | 0 |
| vertical | L2 | 1 | 1 |
| vertical | L3 | 6 | 6 |
| vertical | L4 | 7 | 6 |

## Targeted reruns

The checks in [MIGRATION_NOTES.md](MIGRATION_NOTES.md) identified two targeted
reruns needed to make every retained result directly attributable to the unified
implementation: vertical Wavelet, and L1 cutoff calibration followed by L1 Monte
Carlo for both masks. No complete-study rerun is implied.
