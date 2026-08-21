# Boostlet-based Wavefield Super-resolution

Python implementation of Boostlet-based reconstruction for incomplete, noisy
acoustic wavefields. Linear interpolation, wavelet, and Shearlet baselines are
included for comparison.

The repository contains source code and small configuration files only. The NBI
input HDF5 file and all generated outputs are deliberately excluded from Git.

## Contents

```text
.
├── configs/                   # Main, calibration, and small smoke-test settings
├── src/
│   ├── boostlet_reconstruction/  # Data loading, reconstruction, and CLI
│   └── pyshearlab/               # Vendored dependency for the Shearlet baseline
└── tests/                     # Deterministic unit tests
```

`configs/paper.json` defines the main experimental settings. `configs/smoke.json`
is a small configuration for local checks with compatible input data.

## Installation

The recorded study environment uses Python 3.10. The package supports Python
versions 3.10 through 3.12. With Conda:

```bash
conda env create -f environment.yml
conda activate boostlet-wavefield-sr
```

Or with pip:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Input data

Place the local NBI line-array HDF5 file at `data/rir_NBI_line.h5`, or set
`dataset.path` in a configuration file. The file must contain:

```text
/line02/impulse_response
/line02/posRIR
```

The repository does not download or redistribute this dataset.

## Running a reconstruction

The package provides two commands after installation. Boostlet methods with the
default adaptive cutoff require a matching cutoff table first:

```bash
boostlet-calibrate --mask-type random --level 3 --sampling-ratio 0.3
boostlet-run --method boostlet_l3 --mask-type random --timing late --sampling-ratio 0.3
```

Outputs are written below `outputs/`, which is ignored by Git. Use `--config` to
select another configuration, and `--help` to see the complete command options.

## Method summary

All methods share the same input windows, sampling masks, noise realization, and
metrics. The main configuration evaluates random space-time and vertical receiver
sampling over fixed Boostlet levels L1--L4.

- **Boostlet:** FFT-based discrete dictionary with Meyer radial and rapidity
  windows. A separate cutoff calibration can suppress high-frequency atoms.
- **Linear:** far-field cone projection in the two-dimensional Fourier domain.
- **Wavelet:** PyWavelets decomposition with FISTA reconstruction and L-curve
  parameter selection.
- **Shearlet:** pyShearLab operator with the same sparse solver.

The input is resampled from 48 kHz to `c / dx`, then reconstructed in 128-by-128
time-space windows by the main configuration. Exact numerical parameters, masks,
and solver settings are explicit in `configs/paper.json`.

## Tests

```bash
python -m pip install -e '.[test]'
pytest
```

## License and attribution

Copyright (C) 2026 Ryuto Saeki. This project is licensed under GPL-3.0-or-later;
see [LICENSE](LICENSE). Please cite it using [CITATION.cff](CITATION.cff).

The Shearlet baseline vendors GPL-licensed pyShearLab source under
`src/pyshearlab/`. Boostlet and pyShearLab attribution is recorded in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
