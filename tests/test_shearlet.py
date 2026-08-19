import numpy as np

from boostlet_reconstruction.transforms.shearlet import ShearletOperator


def test_vendored_shearlet_runs_with_numpy_two() -> None:
    operator = ShearletOperator((64, 64), scales=1, removed_indices=[2])
    image = np.random.RandomState(12).normal(size=(64, 64))
    coefficients = operator.analysis(image)
    masked = operator.mask_coefficients(coefficients)
    reconstruction = operator.synthesis(masked)
    assert coefficients.shape[:2] == image.shape
    assert np.all(masked[:, :, 2] == 0.0)
    assert reconstruction.shape == image.shape
    assert np.isfinite(reconstruction).all()
