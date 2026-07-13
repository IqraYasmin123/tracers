# Module 4 — Adversarial Attack Generation

## Goal

Generate the adversarial examples that Modules 5 (detection), 6 (attribution), and 7
(reconstruction) all depend on. Without this module, TRACER has nothing to detect.

## Design

```
BaseAttack (abstract interface)
    └── generate(vlm, pixel_values, text_embeds) -> perturbed pixel_values

FGSMAttack(BaseAttack)  — single gradient step, fast, weaker
PGDAttack(BaseAttack)   — iterative, stronger, harder to detect
AttackConfig            — epsilon, alpha, steps
AttackGenerationError   — module-specific exception
similarity_loss()       — shared untargeted attack loss
```

### Threat model: untargeted, caption-degrading

Both attacks reduce the cosine similarity between an image and its **true** caption — an
untargeted attack. This is the realistic scenario for a forensics tool: an attacker degrading
correct image-text understanding generally, without knowing in advance what captions a
downstream system will use. (A targeted attack — forcing the model toward one specific wrong
label — is a reasonable future extension, not required here.)

### Why `epsilon` bounds matter

`epsilon` (L-infinity norm) caps the maximum per-pixel change. This is what keeps an attack
"adversarial" rather than "just a different image" — real adversarial examples are supposed
to look visually identical to a human while fooling the model. Every test in
`tests/test_attacks.py` explicitly checks the perturbation never exceeds this bound.

### FGSM vs PGD, concretely

- FGSM: one step, `perturbed = image + epsilon * sign(gradient)`
- PGD: `steps` repetitions of a smaller step (`alpha`), each one re-projected back into the
  epsilon-ball around the original image. The projection step is what prevents the
  perturbation from drifting outside the allowed budget despite taking many steps.

### A required change to Module 2

Building this module surfaced a real gap in Module 2: `CLIPVLM.encode_image()` always ran
inference in `torch.no_grad()`, which is correct for pure detection but **breaks attacks
entirely** — FGSM/PGD need gradients flowing back to the pixel values. Fixed by adding a
`requires_grad: bool = False` parameter to `encode_image`/`encode_text` in both `BaseVLM` and
`CLIPVLM` — defaulting to `False` so nothing in Module 2's existing tests or usage changed,
while `similarity_loss()` (used only inside attacks) explicitly passes `requires_grad=True`.
This is a legitimate example of an interface evolving as new requirements are discovered —
worth mentioning in your report as intentional design, not a bug being patched over.

### Testing without a real CLIP download

`tests/test_attacks.py` defines a minimal in-memory `FakeVLM(BaseVLM)` — mean-pools pixel
values and projects them through a small fixed matrix to get an embedding. This is a direct
demonstration of the **Liskov Substitution Principle**: `FGSMAttack`/`PGDAttack` are written
against `BaseVLM`, so they work correctly against *any* conforming implementation, real or
fake, with no special-casing. This keeps the whole attack test suite fast and
network-independent, while still genuinely exercising the real attack math.

**A real bug this caught during development:** the first version of `FakeVLM` used an
all-ones projection matrix, which made every output dimension identical regardless of input —
collapsing to a constant vector after normalization, with zero gradient almost everywhere.
Tests correctly failed (`FGSM did not change the image`), which is exactly what a test suite
is supposed to catch. Fixed by using a fixed random (non-degenerate) projection matrix
instead. Worth mentioning in your viva: a test failing because your *test* had a bug, not your
production code, is a normal and healthy part of TDD — the fix was in `FakeVLM`, not in
`FGSMAttack`/`PGDAttack`.

## Testing Strategy

```bash
pytest tests/test_attacks.py -v   # 11 tests, all self-contained, no CLIP download needed
```

Verified: all 11 tests pass, including real gradient-direction and epsilon-bound checks.

## Completion Checklist

- [x] `BaseAttack` interface defined
- [x] `FGSMAttack` implementation, epsilon-bounded, verified reduces similarity
- [x] `PGDAttack` implementation, epsilon-bounded even with oversized `alpha`, verified
      reduces similarity
- [x] `BaseVLM`/`CLIPVLM` extended with `requires_grad` support (Module 2 tests still pass)
- [x] 11 unit tests, all passing, no network dependency
- [ ] Real attacks run against real CLIP + real Flickr8k images in Colab (do this yourself —
      see `notebooks/04_adversarial_attacks.ipynb`)
