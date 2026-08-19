# SPDX-License-Identifier: GPL-3.0-or-later
"""Metrics used in the Monte Carlo study."""

from __future__ import annotations

import numpy as np
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


def reconstruction_metrics(reference: np.ndarray, reconstruction: np.ndarray) -> dict[str, float]:
    denominator = np.linalg.norm(reference.ravel())
    if denominator == 0:
        raise ValueError("RRMSE is undefined for an all-zero reference")
    rrmse = 100.0 * np.linalg.norm((reference - reconstruction).ravel()) / denominator
    psnr = peak_signal_noise_ratio(reference, reconstruction, data_range=1.0)
    ssim = structural_similarity(reference, reconstruction, data_range=1.0)
    error_variance = float(np.var(reference - reconstruction))
    output_snr = (
        np.inf
        if error_variance < 1e-12
        else 10.0 * np.log10(float(np.var(reconstruction)) / error_variance)
    )
    return {
        "RRMSE": float(rrmse),
        "PSNR": float(psnr),
        "SSIM": float(ssim),
        "Output_SNR": float(output_snr),
    }
