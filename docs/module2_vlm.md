# Module 2 — Vision-Language Model Integration

## Goal

Wrap CLIP behind a clean, testable, swappable interface that every later AI-engine module
(detection, attribution, reconstruction) depends on — without depending on CLIP directly.

## Design

```
BaseVLM (abstract interface)
    ├── preprocess_image(image) -> pixel_values
    ├── encode_image(pixel_values) -> normalized image embedding
    ├── encode_text(texts) -> normalized text embedding
    ├── similarity(image_embeds, text_embeds) -> cosine similarity
    └── get_vision_attentions(pixel_values) -> per-layer attention tensors

CLIPVLM(BaseVLM)  — concrete implementation using transformers' CLIPModel/CLIPProcessor
VLMConfig         — configuration dataclass (model name, device, freeze_weights)
VLMLoadError / VLMInferenceError — module-specific exceptions
```

### Dependency Inversion Principle in practice

Modules 5–8 will be written against `BaseVLM`, not `CLIPVLM`. Concretely:

```python
# Good — Module 5's detector depends on the abstraction:
def compute_entropy(vlm: BaseVLM, pixel_values):
    attentions = vlm.get_vision_attentions(pixel_values)
    ...

# Not this — would hard-couple detection logic to CLIP specifically:
def compute_entropy(clip_model: CLIPModel, pixel_values):
    ...
```

This means a future "Module 2b: BLIP-2 backend" (explicitly listed as a future-work extension,
not a core requirement) would only require writing `BLIP2VLM(BaseVLM)` — Modules 5–8 would not
need a single line changed.

### Why L2-normalize embeddings inside `encode_image`/`encode_text`

CLIP's similarity is defined as cosine similarity. Normalizing once, inside the encoder methods,
means every caller (`similarity()`, and later the detection/attribution modules) can use a plain
dot product and never has to remember to normalize themselves — a correctness guarantee baked
into the interface rather than left as caller responsibility.

### Handling `transformers` API drift

Different `transformers` versions have returned `get_image_features()`/`get_text_features()` as
either a plain `torch.Tensor` or a `ModelOutput` object (this bit us for real during Module 1's
environment check — see the bug fix in `00_colab_bootstrap.ipynb`). `CLIPVLM._extract_embeds()`
handles both cases so the rest of the codebase doesn't need to know which `transformers` version
is installed.

### Error handling

- `VLMLoadError` — raised if the model fails to load (bad model name, no network, OOM). The
  backend (Module 9) will catch this and return a 503-style "AI engine unavailable" response.
- `VLMInferenceError` — raised if a forward pass fails (bad input). The backend will catch this
  and return a 422-style "invalid input" response.

Neither is a bare `except Exception` — this is deliberate so calling code can respond
differently to "the model won't load at all" vs "this specific image caused a problem."

## Testing Strategy

- **Unit tests** (`test_vlm_config_*`) — no model download, no network, run in milliseconds.
  These test configuration logic only.
- **Integration tests** (`@pytest.mark.integration`) — load the real CLIP model from Hugging
  Face and test actual encoding/similarity/attention extraction. Slower, need network access.

```bash
pytest -m "not integration"   # fast, run constantly during development
pytest -m integration         # slower, run before considering the module done
pytest                        # everything
```

## Completion Checklist

- [x] `BaseVLM` interface defined
- [x] `CLIPVLM` implementation complete
- [x] Unit tests passing
- [x] Integration tests written (run these yourself in Colab with network access — see
      `notebooks/02_vlm_integration.ipynb`)
- [x] First real inference demonstrated (zero-shot classification in the notebook)
- [x] Vision-encoder attention extraction confirmed working (needed by Modules 5–6)
