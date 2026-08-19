# SPDX-License-Identifier: GPL-3.0-or-later
"""Discrete Boostlet dictionary and FFT-based analysis/synthesis.

This module is a cleaned Python implementation of the Boostlet construction
used in the study. See THIRD_PARTY_NOTICES.md for upstream attribution.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BoostletDictionary:
    filters: np.ndarray
    peak_radii: np.ndarray
    k_grid: np.ndarray
    omega_grid: np.ndarray

    @property
    def atom_count(self) -> int:
        return int(self.filters.shape[2])

    def subset_by_cutoff(self, cutoff_ratio: float) -> "BoostletDictionary":
        keep = self.peak_radii <= cutoff_ratio
        keep[0] = True
        return BoostletDictionary(
            filters=self.filters[:, :, keep],
            peak_radii=self.peak_radii[keep],
            k_grid=self.k_grid,
            omega_grid=self.omega_grid,
        )


def meyer_nu(value: np.ndarray | float) -> np.ndarray:
    value = np.asarray(value)
    output = np.empty_like(value, dtype=float)
    output[value < 0.0] = 0.0
    middle = (value >= 0.0) & (value <= 1.0)
    x = value[middle]
    output[middle] = 35.0 * x**4 - 84.0 * x**5 + 70.0 * x**6 - 20.0 * x**7
    output[value > 1.0] = 1.0
    return output


def radial_wavelet(radius: np.ndarray) -> np.ndarray:
    absolute = np.abs(radius)
    output = np.zeros_like(radius, dtype=float)
    lower = (absolute >= 1.0 / 3.0) & (absolute < 2.0 / 3.0)
    output[lower] = np.sin(0.5 * np.pi * meyer_nu(3.0 * absolute[lower] - 1.0))
    upper = (absolute >= 2.0 / 3.0) & (absolute <= 4.0 / 3.0)
    output[upper] = np.cos(0.5 * np.pi * meyer_nu(1.5 * absolute[upper] - 1.0))
    return output


def radial_scaling(radius: np.ndarray) -> np.ndarray:
    absolute = np.abs(radius)
    output = np.zeros_like(radius, dtype=float)
    center = absolute <= 1.0 / 3.0
    output[center] = 1.0
    transition = (absolute > 1.0 / 3.0) & (absolute <= 2.0 / 3.0)
    output[transition] = np.cos(
        0.5 * np.pi * meyer_nu(3.0 * absolute[transition] - 1.0)
    )
    return output


def rapidity_window(
    theta: np.ndarray,
    half_width: float,
    alpha: float = 1.0,
    center: float = 0.0,
) -> np.ndarray:
    normalized = np.abs(theta - center) / max(1e-12, half_width)
    return np.sqrt(np.maximum(0.0, meyer_nu(alpha * (1.0 - normalized))))


def _near_field_coordinates(
    k_grid: np.ndarray, omega_grid: np.ndarray, epsilon: float = 1e-12
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mask = np.abs(k_grid) > np.abs(omega_grid)
    radius = np.zeros_like(k_grid, dtype=float)
    theta = np.zeros_like(k_grid, dtype=float)
    if np.any(mask):
        k = k_grid[mask]
        omega = omega_grid[mask]
        radius[mask] = np.sqrt(np.maximum(0.0, k * k - omega * omega))
        denominator = np.where(np.abs(k) < epsilon, np.sign(k) * epsilon, k)
        theta[mask] = np.arctanh(np.clip(omega / denominator, -1.0 + 1e-12, 1.0 - 1e-12))
    return radius, theta, mask


def _far_field_coordinates(
    k_grid: np.ndarray, omega_grid: np.ndarray, epsilon: float = 1e-12
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mask = np.abs(omega_grid) > np.abs(k_grid)
    radius = np.zeros_like(k_grid, dtype=float)
    theta = np.zeros_like(k_grid, dtype=float)
    if np.any(mask):
        k = k_grid[mask]
        omega = omega_grid[mask]
        radius[mask] = np.sqrt(np.maximum(0.0, omega * omega - k * k))
        denominator = np.where(np.abs(omega) < epsilon, np.sign(omega) * epsilon, omega)
        theta[mask] = np.arctanh(np.clip(k / denominator, -1.0 + 1e-12, 1.0 - 1e-12))
    return radius, theta, mask


def _centers_for_band(
    radial_band: np.ndarray,
    cone_mask: np.ndarray,
    unified_radius: np.ndarray,
    maximum_radius: float,
    half_width: float,
) -> np.ndarray:
    support = (radial_band > 1e-12) & cone_mask
    if not np.any(support):
        return np.array([], dtype=float)
    minimum_radius = float(np.min(unified_radius[support]))
    ratio = maximum_radius / max(1e-12, minimum_radius)
    if ratio <= 1.0:
        return np.array([], dtype=float)
    safe_maximum = max(0.0, float(np.arccosh(ratio)) - half_width)
    count = int(np.floor(safe_maximum / max(1e-12, half_width)))
    return np.arange(-count, count + 1, dtype=int) * half_width


def _angular_atoms(
    radial_band: np.ndarray,
    level: int,
    theta: np.ndarray,
    cone_mask: np.ndarray,
    unified_radius: np.ndarray,
    maximum_radius: float,
    h0: float,
    alpha: float,
) -> list[np.ndarray]:
    half_width = float(h0) * (1.5**level)
    centers = _centers_for_band(
        radial_band, cone_mask, unified_radius, maximum_radius, half_width
    )
    if centers.size == 0:
        return []
    angular = [
        rapidity_window(theta, half_width, alpha, float(center)) * cone_mask.astype(float)
        for center in centers
    ]
    denominator = np.sqrt(np.sum(np.stack(angular, axis=0) ** 2, axis=0) + 1e-12)
    return [radial_band * window / denominator for window in angular]


def build_boostlet_dictionary(
    size: int = 128,
    level_count: int = 3,
    h0: float = 0.25,
    alpha: float = 1.0,
    use_top_cap: bool = True,
    maximum_radius: float = 1.0,
) -> BoostletDictionary:
    """Build the no-wall-taper hybrid dictionary used for L1--L4."""
    if size <= 0 or level_count < 1:
        raise ValueError("size and level_count must be positive")
    axis = np.linspace(-maximum_radius, maximum_radius, size)
    k_grid, omega_grid = np.meshgrid(axis, axis, indexing="xy")
    unified_radius = np.sqrt(np.abs(k_grid * k_grid - omega_grid * omega_grid))
    _, near_theta, near_mask = _near_field_coordinates(k_grid, omega_grid)
    _, far_theta, far_mask = _far_field_coordinates(k_grid, omega_grid)

    scaling = radial_scaling((2.0 ** (level_count - 1)) * unified_radius)
    bands = [radial_wavelet((2.0**level) * unified_radius) for level in range(level_count)]
    if use_top_cap:
        residual = np.maximum(0.0, 1.0 - scaling**2 - sum(band**2 for band in bands))
        bands_with_cap = bands + [np.sqrt(residual)]
    else:
        bands_with_cap = bands

    near_levels: list[list[np.ndarray]] = []
    far_levels: list[list[np.ndarray]] = []
    for level, radial_band in enumerate(bands_with_cap):
        near_levels.append(
            _angular_atoms(
                radial_band,
                level,
                near_theta,
                near_mask,
                unified_radius,
                maximum_radius,
                h0,
                alpha,
            )
        )
        far_levels.append(
            _angular_atoms(
                radial_band,
                level,
                far_theta,
                far_mask,
                unified_radius,
                maximum_radius,
                h0,
                alpha,
            )
        )

    atoms = [scaling]
    for group in near_levels + far_levels:
        atoms.extend(group)
    filters = np.stack(atoms, axis=-1)
    peak_radii = [0.0]
    for atom in atoms[1:]:
        peak = np.unravel_index(int(np.argmax(np.abs(atom))), atom.shape)
        peak_radii.append(
            max(abs(float(k_grid[peak])), abs(float(omega_grid[peak]))) / maximum_radius
        )
    return BoostletDictionary(
        filters=filters,
        peak_radii=np.asarray(peak_radii),
        k_grid=k_grid,
        omega_grid=omega_grid,
    )


def parseval_error(dictionary: BoostletDictionary) -> float:
    sum_of_squares = np.sum(dictionary.filters**2, axis=2)
    light_cone = np.sqrt(np.abs(dictionary.k_grid**2 - dictionary.omega_grid**2)) < 1e-9
    errors = np.where(light_cone, np.nan, sum_of_squares - 1.0)
    return float(np.nanmax(np.abs(errors)))


class BoostletOperator:
    def __init__(
        self,
        dictionary: BoostletDictionary,
        removed_indices: tuple[int, ...] | list[int] = (),
    ):
        self.dictionary = dictionary
        self.filters = dictionary.filters
        self.removed_indices = tuple(sorted(set(map(int, removed_indices))))
        self.spatial_size = self.filters.shape[0] * self.filters.shape[1]

    def analysis(self, image: np.ndarray) -> np.ndarray:
        spectrum = np.fft.fftshift(np.fft.fft2(image.reshape(self.filters.shape[:2])))
        coefficients = np.empty_like(self.filters, dtype=float)
        for index in range(self.filters.shape[2]):
            coefficients[:, :, index] = np.real(
                np.fft.ifft2(np.fft.ifftshift(spectrum * self.filters[:, :, index]))
            )
        return np.transpose(coefficients, (2, 0, 1)).ravel()

    def synthesis(self, coefficients: np.ndarray) -> np.ndarray:
        blocks = coefficients.reshape(
            self.filters.shape[2], self.filters.shape[0], self.filters.shape[1]
        )
        blocks = np.transpose(blocks, (1, 2, 0))
        spectrum = np.zeros(self.filters.shape[:2], dtype=complex)
        for index in range(self.filters.shape[2]):
            spectrum += (
                np.fft.fftshift(np.fft.fft2(blocks[:, :, index]))
                * self.filters[:, :, index]
            )
        return np.real(np.fft.ifft2(np.fft.ifftshift(spectrum)))

    def mask_coefficients(self, coefficients: np.ndarray) -> np.ndarray:
        if not self.removed_indices:
            return coefficients
        output = coefficients.copy()
        for index in self.removed_indices:
            if 0 <= index < self.filters.shape[2]:
                start = index * self.spatial_size
                output[start : start + self.spatial_size] = 0.0
        return output
