import numpy as np

from boostlet_reconstruction.transforms.boostlet import (
    BoostletOperator,
    build_boostlet_dictionary,
    parseval_error,
)


def test_dictionary_and_cutoff_are_well_formed() -> None:
    dictionary = build_boostlet_dictionary(size=32, level_count=2)
    assert dictionary.filters.shape[:2] == (32, 32)
    assert dictionary.atom_count == len(dictionary.peak_radii)
    assert dictionary.atom_count > 1
    assert dictionary.peak_radii[0] == 0.0
    assert parseval_error(dictionary) < 1e-6

    subset = dictionary.subset_by_cutoff(0.5)
    assert 1 <= subset.atom_count <= dictionary.atom_count
    assert np.all(subset.peak_radii <= 0.5)


def test_coefficient_block_masking() -> None:
    dictionary = build_boostlet_dictionary(size=16, level_count=1)
    operator = BoostletOperator(dictionary, removed_indices=[1])
    coefficients = np.ones(dictionary.atom_count * 16 * 16)
    masked = operator.mask_coefficients(coefficients)
    assert np.all(masked[16 * 16 : 2 * 16 * 16] == 0.0)
    assert np.all(masked[: 16 * 16] == 1.0)


def test_analysis_and_synthesis_shapes() -> None:
    dictionary = build_boostlet_dictionary(size=16, level_count=1)
    operator = BoostletOperator(dictionary)
    image = np.random.RandomState(3).normal(size=(16, 16))
    coefficients = operator.analysis(image)
    reconstruction = operator.synthesis(coefficients)
    assert coefficients.shape == (dictionary.atom_count * 16 * 16,)
    assert reconstruction.shape == image.shape
    assert np.isfinite(reconstruction).all()
