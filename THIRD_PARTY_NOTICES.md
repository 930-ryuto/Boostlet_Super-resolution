# Third-party notices

## Boostlets

The Boostlet construction in `src/boostlet_reconstruction/transforms/boostlet.py`
is a cleaned Python implementation of the transform used in this research, based
on Boostlets research software by Elias Zea, Marco Laudato, and Joakim Andén.

Upstream source:

<https://github.com/eliaszea/Boostlets_SparsityAnalysis>

The upstream repository is distributed under GNU GPL v3 or later. This project
retains compatible GPL-3.0-or-later licensing and identifies the adaptation in
the relevant source module.

## pyShearLab

Shearlet reconstruction depends on Stefan Loock's pyShearLab:

<https://github.com/stefanloock/pyshearlab>

pyShearLab is distributed under GNU GPL v3. The exact source used by this study
is vendored in `src/pyshearlab/` because upstream tuple arithmetic is incompatible
with NumPy 2 and one two-dimensional padding index required correction. The
vendored package includes its upstream `LICENSE` and `copyright.txt`; changed
files carry modification notices.

## Scientific Python dependencies

NumPy, SciPy, pandas, h5py, PyWavelets, scikit-image, matplotlib, and tqdm are
installed as external dependencies. Refer to each package's distribution for its
license and copyright notices.
