import numpy as np

from boostlet_reconstruction.analysis import holm_adjust


def test_holm_adjustment_is_monotone_in_sorted_p_values() -> None:
    raw = np.array([0.04, 0.001, 0.02, 0.5])
    adjusted = holm_adjust(raw)
    order = np.argsort(raw)
    assert np.all(np.diff(adjusted[order]) >= 0.0)
    assert np.all((adjusted >= raw) & (adjusted <= 1.0))
    np.testing.assert_allclose(adjusted, [0.08, 0.004, 0.06, 0.5])
