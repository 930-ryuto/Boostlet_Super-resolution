import numpy as np

from boostlet_reconstruction.cutoff import hybrid_removed_indices, select_best_cutoff
from boostlet_reconstruction.transforms.boostlet import build_boostlet_dictionary


def test_cutoff_uses_best_per_time_then_nearest_time() -> None:
    rows = [
        {"SNR": 10.0, "Sampling_Ratio": 0.3, "T_start": 600.0, "Cutoff_Pct": 90.0, "RRMSE": 4.0},
        {"SNR": 10.0, "Sampling_Ratio": 0.3, "T_start": 600.0, "Cutoff_Pct": 80.0, "RRMSE": 3.0},
        {"SNR": 10.0, "Sampling_Ratio": 0.3, "T_start": 900.0, "Cutoff_Pct": 70.0, "RRMSE": 2.0},
    ]
    assert select_best_cutoff(rows, 10.0, 0.3, 620) == 80.0
    assert select_best_cutoff(rows, 10.0, 0.3, 880) == 70.0


def test_hybrid_indices_are_a_sorted_union() -> None:
    dictionary = build_boostlet_dictionary(size=16, level_count=1)
    removed = hybrid_removed_indices(dictionary, 50.0, [5, 2, 5])
    assert removed == tuple(sorted(set(removed)))
    assert {2, 5}.issubset(removed)
    cutoff_indices = set(np.flatnonzero(dictionary.peak_radii > 0.5))
    assert cutoff_indices.issubset(removed)
