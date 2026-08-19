from pathlib import Path

import numpy as np

from boostlet_reconstruction.config import load_config
from boostlet_reconstruction.solvers import select_lcurve_lambda
from boostlet_reconstruction.transforms.linear import cone_interpolate


ROOT = Path(__file__).resolve().parents[1]


def test_linear_projection_is_real_and_shape_preserving() -> None:
    image = np.random.RandomState(8).normal(size=(12, 16))
    reconstructed = cone_interpolate(image)
    assert reconstructed.shape == image.shape
    assert np.isrealobj(reconstructed)
    assert np.isfinite(reconstructed).all()


def test_lcurve_fallback_selects_middle_lambda() -> None:
    solver = load_config(ROOT / "configs/paper.json").solver
    lambdas = np.asarray(solver.lambda_factors)
    selected, curvature = select_lcurve_lambda(
        np.zeros_like(lambdas), np.full_like(lambdas, -2.0), lambdas, solver
    )
    assert selected == lambdas[len(lambdas) // 2]
    assert np.all(curvature == 0.0)
