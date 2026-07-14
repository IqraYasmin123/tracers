# Module 5 — Adversarial Detection Engine

## Goal

Detect whether an input image has been adversarially manipulated, using only the target
VLM's own internal attention behavior — no watermarking, no access to the attack generation
process. This is the core claim of your abstract; this module is where it gets implemented
and empirically tested.

## Design

```
compute_entropy_from_attentions(attentions) -> [batch, num_layers]
    Pure math, zero VLM dependency — unit tested with hand-crafted tensors.

extract_attention_entropy(vlm, pixel_values) -> [batch, num_layers]
    Thin wrapper connecting the math to a real BaseVLM (Module 2).

EntropyClassifier(BaseDetector)
    Generic MLP over entropy features. Same class, two roles depending on training labels:
        - fit(X, y) with y in {"clean","adversarial"}  -> binary detector
        - fit(X, y) with y in {"clean","fgsm","pgd"}    -> attack-type classifier
```

### Why one classifier class, not two

"Detection" and "attack classification" are the same underlying task (entropy features ->
label) with a different number of classes. `sklearn.MLPClassifier` already handles binary and
multi-class classification transparently based on the labels you fit it with — writing a
second class for "the 3-class version" would be duplicated code with no behavioral
difference. This is worth stating explicitly in your report as a deliberate design choice.

### Verifying the methodology analytically before trusting real data

Before testing against real CLIP attention weights, `compute_entropy_from_attentions` is
tested against **hand-crafted tensors where the correct answer is known from probability
theory**:
- A uniform attention distribution over N tokens has entropy exactly `log(N)` — the
  theoretical maximum.
- A one-hot (fully concentrated) distribution has entropy exactly 0 — the theoretical
  minimum.

Both are checked exactly (`torch.allclose`), not just "roughly". This matters because it
proves the entropy *formula* is implemented correctly, independent of whether real CLIP
attention happens to separate clean from adversarial well — those are two different claims,
and conflating them would make a bug in the math indistinguishable from a bug in the
underlying hypothesis.

### Classifier plumbing tested with synthetic data, not real features

`EntropyClassifier`'s fit/predict/predict_proba/save/load are tested against synthetic,
clearly-separated Gaussian clusters — this checks the *plumbing* (does save/load round-trip
correctly? does an unfitted model raise the right error?) independent of whether real
attention-entropy features happen to be separable. **Real separability is an empirical
question answered in Colab against real CLIP features on real Flickr8k images plus real
FGSM/PGD attacks from Module 4** — see `notebooks/05_detection.ipynb` and don't take a passing
unit test suite as proof the detector works on real data; run the notebook.

## Testing Strategy

```bash
pytest tests/test_detection.py -v   # 12 tests, all self-contained, no network needed
```

## Completion Checklist

- [x] `compute_entropy_from_attentions` — analytically verified against known entropy values
- [x] `EntropyClassifier` — binary detection and multi-class attack classification both tested
- [x] Save/load round-trip verified
- [x] 12 unit tests passing, no regressions in Modules 2-4 (40 total passing)
- [ ] Real detection accuracy measured against real CLIP + real Flickr8k + real FGSM/PGD
      attacks (do this yourself — see `notebooks/05_detection.ipynb`)
