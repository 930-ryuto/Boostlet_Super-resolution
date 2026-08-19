# SPDX-License-Identifier: GPL-3.0-or-later
"""FISTA reconstruction and L-curve parameter selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.stats import median_abs_deviation

from .config import SolverConfig
from .metrics import reconstruction_metrics


class SparseOperator(Protocol):
    def analysis(self, image: np.ndarray) -> np.ndarray: ...
    def synthesis(self, coefficients: np.ndarray) -> np.ndarray: ...
    def mask_coefficients(self, coefficients: np.ndarray) -> np.ndarray: ...


@dataclass(frozen=True)
class LambdaSweepResult:
    auto_reconstruction: np.ndarray
    oracle_reconstruction: np.ndarray
    auto_lambda: float
    oracle_lambda: float
    auto_residual_log10: float
    auto_solution_log10: float
    auto_metrics: dict[str, float]
    oracle_metrics: dict[str, float]


def soft_threshold(coefficients: np.ndarray, threshold: float) -> np.ndarray:
    return np.sign(coefficients) * np.maximum(np.abs(coefficients) - threshold, 0.0)


def fista(
    observed: np.ndarray,
    mask: np.ndarray,
    lambda_factor: float,
    operator: SparseOperator,
    config: SolverConfig,
) -> tuple[np.ndarray, np.ndarray]:
    estimate = np.zeros_like(observed)
    momentum_image = estimate.copy()
    momentum = 1.0
    sigma = lambda_factor * median_abs_deviation(observed[mask > 0], scale="normal")
    threshold = sigma * np.sqrt(2.0 * np.log(observed.size)) * config.step_size

    for _ in range(config.max_iterations):
        gradient = (momentum_image * mask - observed) * mask
        proximal_input = momentum_image - config.step_size * gradient
        coefficients = operator.mask_coefficients(operator.analysis(proximal_input))
        thresholded = soft_threshold(coefficients, threshold)
        updated = np.asarray(operator.synthesis(thresholded)).reshape(observed.shape)
        next_momentum = (1.0 + np.sqrt(1.0 + 4.0 * momentum**2)) / 2.0
        momentum_image = updated + ((momentum - 1.0) / next_momentum) * (updated - estimate)
        estimate = updated
        momentum = next_momentum
    return estimate, thresholded


def select_lcurve_lambda(
    residual_log10: np.ndarray,
    solution_log10: np.ndarray,
    lambdas: np.ndarray,
    config: SolverConfig,
) -> tuple[float, np.ndarray]:
    valid = solution_log10 > config.lcurve_min_log_solution
    if np.count_nonzero(valid) < 8:
        return float(lambdas[len(lambdas) // 2]), np.zeros_like(lambdas)

    log_lambda = np.log10(lambdas)
    residual_spline = UnivariateSpline(
        log_lambda[valid], residual_log10[valid], s=config.lcurve_smoothing
    )
    solution_spline = UnivariateSpline(
        log_lambda[valid], solution_log10[valid], s=config.lcurve_smoothing
    )
    residual_d1 = residual_spline.derivative(1)(log_lambda)
    residual_d2 = residual_spline.derivative(2)(log_lambda)
    solution_d1 = solution_spline.derivative(1)(log_lambda)
    solution_d2 = solution_spline.derivative(2)(log_lambda)
    denominator = (residual_d1**2 + solution_d1**2) ** 1.5
    with np.errstate(divide="ignore", invalid="ignore"):
        curvature = (residual_d1 * solution_d2 - residual_d2 * solution_d1) / denominator
    curvature = np.nan_to_num(curvature, nan=0.0, posinf=0.0, neginf=0.0)
    curvature[0] = 0.0
    curvature[-1] = 0.0
    curvature[~valid] = 0.0
    return float(lambdas[int(np.argmin(curvature))]), curvature


def sweep_lambdas(
    noisy: np.ndarray,
    mask: np.ndarray,
    reference: np.ndarray,
    operator: SparseOperator,
    config: SolverConfig,
) -> LambdaSweepResult:
    observed = noisy * mask
    lambdas = np.asarray(config.lambda_factors, dtype=float)
    reconstructions: list[np.ndarray] = []
    metrics: list[dict[str, float]] = []
    residuals: list[float] = []
    solutions: list[float] = []

    for lambda_factor in lambdas:
        reconstruction, coefficients = fista(observed, mask, lambda_factor, operator, config)
        residuals.append(
            np.log10(max(float(np.linalg.norm(mask * (reconstruction - noisy))), 1e-10))
        )
        solutions.append(np.log10(max(float(np.sum(np.abs(coefficients))), 1e-10)))
        reconstructions.append(reconstruction)
        metrics.append(reconstruction_metrics(reference, reconstruction))

    residual_array = np.asarray(residuals)
    solution_array = np.asarray(solutions)
    auto_lambda, _ = select_lcurve_lambda(residual_array, solution_array, lambdas, config)
    auto_index = int(np.argmin(np.abs(lambdas - auto_lambda)))
    oracle_index = int(np.argmin([item["RRMSE"] for item in metrics]))
    return LambdaSweepResult(
        auto_reconstruction=reconstructions[auto_index],
        oracle_reconstruction=reconstructions[oracle_index],
        auto_lambda=float(lambdas[auto_index]),
        oracle_lambda=float(lambdas[oracle_index]),
        auto_residual_log10=float(residual_array[auto_index]),
        auto_solution_log10=float(solution_array[auto_index]),
        auto_metrics=metrics[auto_index],
        oracle_metrics=metrics[oracle_index],
    )
