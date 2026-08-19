# Input data

Place the NBI line-array HDF5 file at:

```text
data/rir_NBI_line.h5
```

The file is intentionally excluded from Git. The code expects these datasets:

```text
/line02/impulse_response
/line02/posRIR
```

You may use another location by changing `dataset.path` in the JSON configuration.
The repository neither downloads nor redistributes the input data.
