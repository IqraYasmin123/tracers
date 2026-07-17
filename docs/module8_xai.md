# Module 8 — Explainable AI (XAI)

## Goal

Turn the numeric/visual outputs of Modules 5-7 into a coherent, human-readable "AI reasoning
summary" — what an actual investigator using TRACER would read, not raw probability numbers.
This is the last AI-engine module; Module 9 onward moves into the backend/frontend/database.

## Design

```
ExplanationContext   — plain dataclass: detection verdict/confidence, attack type,
                        attribution method/spread, reconstruction fidelity — all optional
                        except the detection verdict itself
Explanation           — output: one summary sentence + a list of supporting detail sentences
BaseExplainer         — abstract interface
RuleBasedExplainer     — templated, deterministic implementation
confidence_level_from_probability() — "high"/"medium"/"low" categorization
```

### Why rule-based, not LLM-backed

An LLM call would produce more naturally-varied prose, but at real costs for this project:
non-determinism (the same input could produce different explanations on different runs,
making testing awkward and results non-reproducible), an external API dependency (network
access, API keys, cost), and added latency. `RuleBasedExplainer` is fully deterministic —
every one of the 20 tests in `tests/test_xai.py` runs as a plain assertion with no mocking
needed, and completes in 0.07 seconds total. This is a legitimate, defensible design decision
for a forensics tool specifically — you generally want a forensic report to be reproducible
and auditable, not creatively rephrased differently each time you regenerate it.

`BaseExplainer` still exists as an abstract interface, so an LLM-backed explainer could be
added later (e.g. `LLMExplainer(BaseExplainer)`) as an optional richer alternative without
changing any calling code — this is the Dependency Inversion Principle doing real work again.

### Why `ExplanationContext` has zero dependency on the rest of the AI engine

Every field is a plain float, string, or `None` — no `torch.Tensor`, no `BaseVLM`, nothing
from `src.vlm`/`attacks`/`detection`/`attribution`/`reconstruction`. This makes Module 8 the
cleanest-dependency module in the project: its 20 tests run without importing `torch` at all.
Building a real `ExplanationContext` from actual pipeline outputs is orchestration/glue code
that belongs in the calling notebook (or later, the FastAPI backend) — not in this module.

### A concrete example of honest reporting: the reconstruction case

`_explain_reconstruction` explicitly checks whether reconstruction SSIM is *lower* than the
no-reconstruction baseline, and if so, says so directly rather than silently reporting a
number that looks like an improvement. This mirrors the real, honest finding from Module 7
(diffusion inpainting did not improve fidelity for the imperceptible PGD example) — the
explainer is designed to surface that kind of nuance automatically for any future image,
not just describe it after the fact for one example. `test_explainer_flags_reconstruction_
that_did_not_improve` tests this exact scenario using the real numbers from Module 7.

## Testing Strategy

```bash
pytest tests/test_xai.py -v   # 20 tests, 0.07s total, zero ML dependencies
```

## Completion Checklist

- [x] `ExplanationContext` — validated, zero heavy dependencies
- [x] `RuleBasedExplainer` — covers detection, attack-type, attribution, and reconstruction
      sections, each appearing only when relevant data is present
- [x] Honest reconstruction-fidelity reporting verified against the real Module 7 finding
- [x] 20 unit tests, all passing in <0.1s, no regressions (84 total passing across Modules 2-8)
- [ ] Real end-to-end explanation generated for the real PGD-attacked image from Modules 4-7
      — do this yourself, see `notebooks/08_xai.ipynb`
