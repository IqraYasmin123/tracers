"""Image reconstruction (Module 7).

Public API:
    BaseReconstructor          — abstract interface
    DiffusionReconstructor      — Stable Diffusion inpainting implementation
    ReconstructionConfig        — configuration dataclass
    ReconstructionError          — module-specific exception
    heatmap_to_mask              — pure-math heatmap -> binary mask conversion
    compute_reconstruction_metrics — SSIM/PSNR fidelity comparison
    compare_images                — visualization helper

Example:
    >>> from src.reconstruction import DiffusionReconstructor, compute_reconstruction_metrics
    >>> reconstructor = DiffusionReconstructor()
    >>> reconstructed = reconstructor.reconstruct(adversarial_pil_image, heatmap)
    >>> compute_reconstruction_metrics(clean_pil_image, reconstructed)
"""
from .base import BaseReconstructor
from .config import ReconstructionConfig
from .diffusion_reconstructor import DiffusionReconstructor
from .exceptions import ReconstructionError
from .mask import heatmap_to_mask
from .metrics import compute_reconstruction_metrics
from .visualize import compare_images

__all__ = [
    "BaseReconstructor",
    "DiffusionReconstructor",
    "ReconstructionConfig",
    "ReconstructionError",
    "heatmap_to_mask",
    "compute_reconstruction_metrics",
    "compare_images",
]
