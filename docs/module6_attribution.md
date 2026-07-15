# Module 6 — Attention Analysis & Heatmap Generation

## Goal

Move from "is this adversarial?" (Module 5) to "*where* in the image is the attack, and what
is the model attending to?" — the forensic localization half of your abstract.

## Design

```
BaseAttribution (abstract interface)
    └── generate(vlm, pixel_values, text_embeds=None) -> AttributionResult

GradientSaliency(BaseAttribution)  — input-gradient sensitivity map
AttentionMap(BaseAttribution)      — raw CLS-token attention visualization
AttributionResult                   — heatmap + method name, with .resized() for overlay
normalize_heatmap()                 — shared min-max normalization
```

### Two complementary signals, not competing ones

- **`GradientSaliency`** answers "what would changing this pixel do to the similarity
  score?" — computed by backpropagating the same `similarity_loss` Module 4's attacks use,
  down to the input pixels. High gradient magnitude = high sensitivity = forensically
  interesting region.
- **`AttentionMap`** answers "what is the model actually looking at right now?" — read
  directly from real attention weights (the CLS token's attention to each image patch), no
  gradients needed at all.

These measure genuinely different things and can disagree — that disagreement is itself
forensically informative (e.g. the model "looking at" one region while being most
"sensitive to" another can indicate exactly where a subtle perturbation is doing its work).
Report both in your results chapter rather than picking one.

### Reusing Module 4's `similarity_loss`

`GradientSaliency` imports `similarity_loss` from `src.attacks.utils` rather than
reimplementing it — the gradient an attacker uses to know which direction to perturb pixels
is the exact same gradient that tells us, forensically, which pixels the model's decision is
most sensitive to. This is a deliberate code-reuse decision, not an accident of module
ordering — worth mentioning in your report as evidence the codebase's dependency structure
(`vlm` → `attacks` → `attribution`) reflects a real conceptual relationship, not just
convenience.

### A named limitation, honestly stated

`GradientSaliency` produces a *sensitivity* map, not a verified ground-truth localization of
exactly which pixels an attacker changed. For a rigorous localization metric, you'd compare
this heatmap against the actual perturbation mask
(`|adversarial_pixels - clean_pixels| > threshold`) via Intersection-over-Union — possible
only for synthetic attacks where you generated the attack yourself and thus know the ground
truth. This is listed as a stretch-goal evaluation in earlier module notebooks; doing it here
would strengthen your results chapter meaningfully if time allows.

### Why `AttentionMap` needs a square-patch-count check

CLIP's vision transformer tokenizes an image into a grid of patches (e.g. 7×7=49 for
ViT-B/32 at 224px with 32px patches) plus one CLS token. Reshaping the CLS token's
patch-attention vector back into a 2D grid for visualization only works if the patch count is
a perfect square — `AttentionMap` explicitly checks this and raises `AttributionError` with a
clear message rather than silently producing a garbled heatmap if a future VLM backbone uses
a non-square patch layout.

## Testing Strategy

```bash
pytest tests/test_attribution.py -v   # 10 tests, all self-contained, no network needed
```

Uses a `FakeVLM` with synthetic (but correctly-shaped) attention tensors, extending the same
pattern from Modules 4 and 5.

## Completion Checklist

- [x] `GradientSaliency` — verified correct shape, values bounded to [0,1]
- [x] `AttentionMap` — verified correct grid reshaping, rejects non-square patch counts
- [x] `AttributionResult.resized()` — verified correct interpolation to arbitrary target size
- [x] 10 unit tests passing, no regressions (50 total passing across Modules 2-6)
- [ ] Real heatmaps generated on the real PGD-attacked image from Module 4/5 (similarity
      0.312 → 0.008) — do this yourself, see `notebooks/06_attribution.ipynb`
