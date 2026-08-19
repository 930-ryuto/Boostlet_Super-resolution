# SPDX-License-Identifier: GPL-3.0-or-later
"""PyWavelets analysis/synthesis adapter."""

from __future__ import annotations

import numpy as np
import pywt


class WaveletOperator:
    def __init__(self, shape: tuple[int, int], name: str = "db38", level: int = 2, mode: str = "periodization"):
        self.shape = shape
        self.wavelet = pywt.Wavelet(name)
        self.level = level
        self.mode = mode
        template = pywt.wavedec2(np.zeros(shape), self.wavelet, level=level, mode=mode)
        array, self.slices = pywt.coeffs_to_array(template)
        self.coefficient_shape = array.shape

    def analysis(self, image: np.ndarray) -> np.ndarray:
        coefficients = pywt.wavedec2(
            image, self.wavelet, level=self.level, mode=self.mode
        )
        array, _ = pywt.coeffs_to_array(coefficients)
        return array.ravel()

    def synthesis(self, coefficients: np.ndarray) -> np.ndarray:
        structured = pywt.array_to_coeffs(
            coefficients.reshape(self.coefficient_shape),
            self.slices,
            output_format="wavedec2",
        )
        image = pywt.waverec2(structured, self.wavelet, mode=self.mode)
        return image[: self.shape[0], : self.shape[1]]

    @staticmethod
    def mask_coefficients(coefficients: np.ndarray) -> np.ndarray:
        return coefficients
