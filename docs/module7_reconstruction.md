# Module 7 — Image Reconstruction

## Goal

Attempt to recover a clean-looking version of an adversarially attacked image, guided by
the attribution heatmap from Module 6 — the last piece of TRACER's end-to-end forensic
pipeline: detect (5) → localize (6) → reconstruct (7).

## Design

```
BaseReconstructor (abstract interface)
    └── reconstruct(image, heatmap, prompt=None) -> reconstructed PIL.Image

DiffusionReconstructor(BaseReconstructor)  — Stable Diffusion inpainting implementation
ReconstructionConfig                        — model name, mask threshold, sampling params
heatmap_to_mask()                           — pure math: heatmap -> binary inpainting mask
compute_reconstruction_metrics()            — pure math: SSIM/PSNR fidelity vs. clean original
compare_images()                            — visualization helper
```

### Testing strategy: why this module is different

Every prior AI-engine module could be fully unit tested, because their core dependency (CLIP,
~600MB) was at least *feasible* to reason about via fakes matching its interface shape. Stable
Diffusion inpainting is several gigabytes — genuinely impractical to load in a fast test suite,
and not something that should run on every `pytest` invocation even if it were fast.

The fix: **dependency injection**. `DiffusionReconstructor.__init__` accepts an optional
`pipeline` argument. Tests inject a lightweight `FakePipeline` that mimics the real
`diffusers` pipeline's call signature (`prompt`, `image`, `mask_image` in, `.images` list out)
without containing any actual model weights. This verifies the real logic that's actually
TRACER's own code — mask construction from the heatmap, prompt resolution, error handling —
without needing the multi-GB dependency at all. The real pipeline is only ever loaded in
Colab, via `notebooks/07_reconstruction.ipynb`.

This is a standard, legitimate testing pattern (mocking/injecting heavy external
dependencies) — worth explicitly naming as such in your report, since it demonstrates
awareness of testing strategy trade-offs rather than just "we didn't test the hard part."

### Why `compute_reconstruction_metrics` caps PSNR instead of returning infinity

Identical images give a PSNR of literally infinite dB (zero mean-squared error). Returning
`float('inf')` from a metrics function is a common source of downstream bugs (breaks JSON
serialization, breaks averaging across many samples, breaks plotting). Capping at 100.0 dB —
far above any realistic non-identical-image score — keeps the function's output always
finite and safely usable, while `SSIM: 1.0` already unambiguously communicates "identical."

### The mask threshold as a genuine trade-off, not just a number

`mask_threshold` (default 0.5) controls how much of the image gets handed to the diffusion
model to regenerate. Too low, and most of the image gets regenerated — the diffusion model
effectively replaces content it never needed to touch, likely *lowering* fidelity to the true
original. Too high, and the actual damaged region might not be fully covered, leaving
adversarial artifacts in the output. This is worth an explicit ablation in your results
chapter if time allows: report reconstruction SSIM/PSNR at a few different threshold values.

## Testing Strategy

```bash
pytest tests/test_reconstruction.py -v   # 14 tests, all self-contained, no model download
```

## Completion Checklist

- [x] `heatmap_to_mask` — verified correct thresholding, rejects invalid ranges
- [x] `compute_reconstruction_metrics` — verified against known cases (identical → perfect,
      very different → poor), verified shape-mismatch error handling
- [x] `DiffusionReconstructor` — plumbing verified via fake pipeline injection (prompt
      passing, mask sizing, error propagation)
- [x] 14 unit tests passing, no regressions (64 total passing across Modules 2-7)
- [ ] Real reconstruction run on the real PGD-attacked image from Modules 4-6, with real
      SSIM/PSNR numbers and a visual clean/adversarial/reconstructed comparison — do this
      yourself, see `notebooks/07_reconstruction.ipynb`
