# Boostlet-based Wavefield Super-resolution

Reproducible research code for comparing Boostlets with linear interpolation,
wavelets, and shearlets in acoustic wavefield reconstruction from incomplete and
noisy measurements.

The repository contains the code required to regenerate the experiments. It does
not contain the input HDF5 file, cutoff/result CSVs, or manuscript. All generated
artifacts are written below `outputs/`, which is excluded from Git.

## Study design

The unified runner uses one shared data, mask, noise, and metric implementation
for every method. The published configuration covers:

- random space-time sampling and vertical receiver sampling;
- early and late response windows;
- sampling ratios 0.3, 0.4, and 0.5;
- input SNRs 0, 5, 10, 15, and 20 dB;
- 100 paired trials per condition;
- Linear, Wavelet, Shearlet, and fixed Boostlet configurations L1--L4.

Each Boostlet level is retained as a separate method. The code does not choose a
level after observing a test result. The frequency-correlation C(f) analysis is
outside the scope of this repository.

## Repository layout

```text
.
├── configs/                   # Paper, calibration, and smoke-test settings
├── data/README.md             # Expected local HDF5 layout
├── docs/                      # Methods and reproducibility documentation
├── scripts/                   # Experiment, aggregation, figure, and audit tools
├── src/boostlet_reconstruction/
│   ├── transforms/            # Linear, Wavelet, Shearlet, and Boostlet operators
│   ├── calibration.py         # Boostlet cutoff calibration
│   ├── experiment.py          # Unified paired Monte Carlo runner
│   ├── sampling.py            # Shared windows, masks, and noise
│   └── solvers.py             # FISTA and L-curve selection
└── tests/                     # Deterministic unit and repository-safety tests
```

## Installation

The recorded environment uses Python 3.10. Create it with Conda:

```bash
conda env create -f environment.yml
conda activate boostlet-wavefield-sr
```

Alternatively:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

The GPL-licensed pyShearLab source used by the study is vendored under
`src/pyshearlab/` with its copyright and license notices. Its small compatibility
changes are documented in the modified source. The package is imported only for
Shearlet jobs.

## Input data

Place the local NBI line-array file at `data/rir_NBI_line.h5`, or edit
`dataset.path` in `configs/paper.json`. The required HDF5 keys and expected layout
are documented in [data/README.md](data/README.md).

The input file is deliberately not downloaded or redistributed by this project.

## Reproduce the study

### 1. Calibrate Boostlet cutoffs

Boostlet L1--L4 use a cutoff selected from a separate oracle calibration sweep.
Generate the 24 independent calibration jobs with:

```bash
python scripts/make_job_matrix.py calibration > calibration_jobs.txt
```

Run each line locally or through a scheduler. A single example is:

```bash
python scripts/run_calibration.py \
  --mask-type random \
  --level 3 \
  --sampling-ratio 0.3
```

Calibration tables are written to `outputs/calibration/`.

### 2. Run the paired Monte Carlo experiments

Print the complete 84-job matrix:

```bash
python scripts/make_job_matrix.py experiment > experiment_jobs.txt
```

Example:

```bash
python scripts/run_experiment.py \
  --method boostlet_l3 \
  --mask-type random \
  --timing late \
  --sampling-ratio 0.3
```

For an array job, use `--trial-start` and `--trial-stop` with non-overlapping,
1-based inclusive trial IDs. Every split consumes the same deterministic random
stream, so its rows match an unsplit run.

### 3. Aggregate and plot

```bash
python scripts/summarize_results.py
python scripts/analyze_results.py
python scripts/make_figures.py
```

The figure script plots all fixed Boostlet levels, without a condition-wise
best-level envelope. The analysis script performs paired comparisons against
Shearlet with condition-wise and global Holm correction, produces mean-RRMSE
rankings, and labels condition-wise best-level selection as exploratory.

## Tests and public-release audit

```bash
python -m pip install -e '.[test]'
pytest
python scripts/check_public_repo.py
```

The audit rejects credential patterns, personal absolute paths, and files larger
than 50 MB. There is no messaging or notification integration in this codebase.

## Configuration and provenance

`configs/paper.json` is the single source of truth for experiment parameters.
See [docs/METHODS.md](docs/METHODS.md) for the numerical pipeline and
[docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) for seeds, pairing, job
splitting, and expected outputs. Two targeted reruns identified while consolidating
the historical scripts are documented in
[docs/MIGRATION_NOTES.md](docs/MIGRATION_NOTES.md). Completed equivalence and
test checks are recorded in [docs/VALIDATION.md](docs/VALIDATION.md).

## License and attribution

Copyright (C) 2026 Ryuto Saeki.

This repository is licensed under GPL-3.0-or-later. Boostlet and pyShearLab
attribution is recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
