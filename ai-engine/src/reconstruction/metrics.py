"""Reconstruction fidelity metrics — how close is the reconstructed image to the true clean
original? Pure algorithmic comparison (scikit-image), no model download needed."""
from __future__ import annotations

import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

from .exceptions import ReconstructionError

_PSNR_CAP = 100.0  # identical images give infinite PSNR; capped so results stay finite/reportable


def compute_reconstruction_metrics(clean: Image.Image, reconstructed: Image.Image) -> dict:
    """Compare a reconstructed image against the true clean original.

    Returns:
        {"SSIM": float in [-1,1] (1.0 = identical), "PSNR": float in dB (higher is better,
        capped at 100.0 for identical images to avoid an unreportable infinity)}
    """
    clean_array = np.array(clean.resize(reconstructed.size))
    recon_array = np.array(reconstructed)

    if clean_array.shape != recon_array.shape:
        raise ReconstructionError(
            f"Shape mismatch: clean image is {clean_array.shape}, reconstructed is "
            f"{recon_array.shape} — cannot compare pixel-wise."
        )

    if np.array_equal(clean_array, recon_array):
        return {"SSIM": 1.0, "PSNR": _PSNR_CAP}

    ssim_value = structural_similarity(clean_array, recon_array, channel_axis=-1, data_range=255)
    psnr_value = peak_signal_noise_ratio(clean_array, recon_array, data_range=255)

    return {"SSIM": float(ssim_value), "PSNR": float(min(psnr_value, _PSNR_CAP))}
