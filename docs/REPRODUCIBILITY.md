# Reproducibility contract

## One unified pipeline

There is a single experiment mode. Method-specific transforms remain separate,
but all methods call the same window loader, random schedule, mask generator,
noise scaling, metrics, output schema, and sparse solver where applicable.

The repository does not preserve week-numbered copies of historical scripts.
Those copies were consolidated into the modules under `src/`.

## Deterministic pairing

For each timing region, `RandomState(42)` first draws all 100 temporal starts and
then all 100 spatial starts. It subsequently draws standard-normal arrays in
trial-then-SNR order. Trial masks use independent `RandomState(trial_index)`
instances. Consequently, every method receives the same window, mask, and noisy
field for a given mask type, timing, ratio, trial, and SNR.

The generator also consumes arrays for trials outside a selected job slice. This
makes a split run identical to the corresponding rows of a complete run.

## Configuration identity

Keep an unchanged copy of `configs/paper.json` with every archived run. Record:

- the Git commit;
- the environment file or `pip freeze` output;
- the input HDF5 checksum maintained by the data owner;
- the exact job matrix;
- scheduler and hardware information.

Do not change a configuration in place after producing results. Copy it to a new
filename and document the reason.

## Output identity

Each experiment file name identifies method, mask, timing, sampling ratio, and
trial range. Before aggregation, `summarize_results.py` rejects duplicate keys
caused by overlapping split jobs.

Expected full primary output size:

```text
2 masks * 2 timings * 3 ratios * 5 SNRs * 7 methods * 100 trials
= 42,000 rows
```

Generated CSVs and figures are intentionally ignored by Git. Archive them with
the manuscript workflow if needed; they are not required in the source-code
repository.

## Fast checks

The unit tests exercise dictionary construction, coefficient masking, transforms,
random schedules, masks, L-curve fallback, cutoff selection, and the release
audit without running the expensive 128-by-128 Monte Carlo matrix.

`configs/smoke.json` reduces the image and iteration counts for an end-to-end
local check after a compatible test HDF5 file has been placed under `data/`.
