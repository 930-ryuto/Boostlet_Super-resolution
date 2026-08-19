# SPDX-License-Identifier: GPL-3.0-or-later
"""pyShearLab analysis/synthesis adapter."""

from __future__ import annotations

import numpy as np


class ShearletOperator:
    def __init__(
        self,
        shape: tuple[int, int],
        scales: int = 2,
        removed_indices: tuple[int, ...] | list[int] = (),
    ):
        try:
            import pyshearlab as psl
            from pyshearlab import pySLFilters as filters
            from pyshearlab import pySLUtilities as utilities
        except ImportError as exc:
            raise ImportError(
                "Shearlet reconstruction requires pyShearLab. Install requirements.txt."
            ) from exc

        lowpass, _ = filters.dfilters("cd", "d")
        directional_filter = utilities.modulate2(lowpass / np.sqrt(2.0), "c")
        self.psl = psl
        self.system = psl.SLgetShearletSystem2D(
            0,
            shape[0],
            shape[1],
            scales,
            directionalFilter=directional_filter,
        )
        self.removed_indices = tuple(map(int, removed_indices))

    def analysis(self, image: np.ndarray) -> np.ndarray:
        return self.psl.SLsheardec2D(image, self.system)

    def synthesis(self, coefficients: np.ndarray) -> np.ndarray:
        return np.real(self.psl.SLshearrec2D(coefficients, self.system))

    def mask_coefficients(self, coefficients: np.ndarray) -> np.ndarray:
        if not self.removed_indices:
            return coefficients
        output = coefficients.copy()
        for index in self.removed_indices:
            if 0 <= index < output.shape[2]:
                output[:, :, index] = 0.0
        return output
