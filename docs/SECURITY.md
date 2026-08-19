# Security and publication checklist

This public codebase contains no notification integration, webhook, credential,
or environment-specific absolute data path.

Before publishing a revision:

1. Run `python scripts/check_public_repo.py`.
2. Run the test suite.
3. Inspect `git status --short` and `git diff --cached`.
4. Confirm that HDF5 files, generated CSVs, figures, job logs, and `.env` files are
   not staged.
5. Review the commit history as well as the current tree; deleting a secret in a
   later commit does not remove it from earlier commits.

If a credential was ever present in a local research script, revoke or rotate it
before making any related repository public. Do not copy the historical scripts
into this repository.
