# Compute and job splitting

The complete cutoff sweep and Monte Carlo grid are computationally expensive.
The code is structured as independent jobs rather than silently spawning local
processes.

`scripts/make_job_matrix.py calibration` prints one command for every combination
of mask type, Boostlet level, and sampling ratio. These jobs must finish before
the corresponding Boostlet Monte Carlo jobs.

`scripts/make_job_matrix.py experiment` prints one command for every combination
of method, mask, timing, and ratio. A command can be divided further with
non-overlapping trial ranges:

```bash
python scripts/run_experiment.py \
  --method shearlet --mask-type random --timing early --sampling-ratio 0.3 \
  --trial-start 1 --trial-stop 20
```

The next job should start at trial 21. Output files include their trial ranges,
and aggregation rejects overlaps.

The code performs no messaging, web requests, or scheduler-specific submission.
Redirect standard output and standard error using the conventions of the local
compute environment.
