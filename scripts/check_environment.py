"""
TRACER — local environment verification script.

Run this after `pip install -r ai-engine/requirements.txt` to confirm your local
(non-Colab) environment is correctly set up before starting Module 2.

Usage:
    python scripts/check_environment.py
"""
import sys
import importlib


REQUIRED_PACKAGES = [
    "torch",
    "torchvision",
    "transformers",
    "diffusers",
    "sklearn",
    "cv2",
    "skimage",
    "matplotlib",
    "plotly",
    "fpdf",
    "gradio",
]


def check_packages() -> list[str]:
    """Return a list of missing package names."""
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    return missing


def check_gpu() -> None:
    import torch

    print(f"Torch version:  {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU device:     {torch.cuda.get_device_name(0)}")
    else:
        print("No GPU detected — CPU-only mode. This is fine for Modules 1-3, "
              "but attack generation and diffusion reconstruction will be slow. "
              "Consider using Google Colab's free GPU for those modules.")


def main() -> int:
    print("=" * 55)
    print("TRACER — ENVIRONMENT CHECK")
    print("=" * 55)
    print(f"Python version: {sys.version.split()[0]}")

    missing = check_packages()
    if missing:
        print(f"\nMISSING PACKAGES: {', '.join(missing)}")
        print("Run: pip install -r ai-engine/requirements.txt")
        return 1

    print("All required packages are installed.\n")
    check_gpu()
    print("\nEnvironment check PASSED. Ready for Module 2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
