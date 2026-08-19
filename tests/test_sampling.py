from pathlib import Path

import numpy as np

from boostlet_reconstruction.config import load_config
from boostlet_reconstruction.sampling import add_awgn, iter_schedule, make_mask


ROOT = Path(__file__).resolve().parents[1]


def test_schedule_is_deterministic_and_trial_then_snr() -> None:
    experiment = load_config(ROOT / "configs/smoke.json").experiment
    first = list(iter_schedule(experiment, "early"))
    second = list(iter_schedule(experiment, "early"))
    assert len(first) == experiment.trials * len(experiment.input_snrs_db)
    assert first[0].trial_id == 1
    assert first[0].t_start == second[0].t_start
    assert first[0].x_start == second[0].x_start
    np.testing.assert_array_equal(first[0].standard_normal, second[0].standard_normal)


def test_mask_counts_and_trial_pairing() -> None:
    random_mask = make_mask("random", 0.3, 16, 20, trial_index=4)
    random_mask_again = make_mask("random", 0.3, 16, 20, trial_index=4)
    vertical_mask = make_mask("vertical", 0.3, 16, 20, trial_index=4)
    assert int(random_mask.sum()) == int(np.rint(0.3 * 16 * 20))
    assert int(vertical_mask.sum()) == int(np.rint(0.3 * 20)) * 16
    np.testing.assert_array_equal(random_mask, random_mask_again)
    assert np.all((vertical_mask.sum(axis=0) == 0) | (vertical_mask.sum(axis=0) == 16))


def test_awgn_uses_the_supplied_realization() -> None:
    clean = np.ones((4, 4))
    normal = np.zeros_like(clean)
    np.testing.assert_array_equal(add_awgn(clean, 10.0, normal), clean)
