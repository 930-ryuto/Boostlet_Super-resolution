# Contributing

Keep experiment changes reproducible and reviewable:

- make numerical parameters explicit in a new JSON configuration;
- add or update tests for numerical behavior;
- do not add input data, generated results, credentials, notifications, or
  machine-specific absolute paths;
- run `pytest` and `python scripts/check_public_repo.py` before opening a change;
- document changes that alter random streams, pairing, transforms, solvers, or
  output columns.

Contributions are accepted under the repository's GPL-3.0-or-later license.
