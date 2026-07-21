# Module 11 — Desktop Dashboard (React)

## Goal

The first client-facing tier: Login, Dashboard, Sidebar, Investigation (upload + results),
and Settings — built with a deliberate dark cybersecurity visual identity, and genuinely
wired to the real Module 9 backend where it matters most (the Investigation page).

## Scope, stated honestly

| Page | Real functionality | Placeholder (arrives later) |
|---|---|---|
| Login | Real client-side validation (email format, password length) | Real JWT auth (Module 16) |
| Dashboard | Real backend health check | Case stats, charts (Modules 12-13) |
| Investigation | **Fully real**: upload → calls `/api/v1/analyze` → displays real verdict, heatmap, explanation, hash | — |
| Settings | Real UI shell | All toggles inert (Module 16) |

The Investigation page is where the actual engineering effort went — it's a genuine,
working integration with everything built in Modules 2-9, not a mockup.

## Design System

### Color — semantically real, not decorative
`#0B0E14` background, `#12151D` panels, `#3DD6C4` cyan accent, plus three verdict colors
(`#5FD98A` clean, `#E85C4A` adversarial, `#E8A83D` warning) that map directly to real
detection states from Modules 5-8. This isn't a generic "dark mode" palette — the tri-color
verdict system is functionally meaningful, driven by the actual data the app displays.

### Type — JetBrains Mono + Inter
Mono for data-like content (verdicts, hashes, case-adjacent numbers) evokes a technical,
evidence-log identity appropriate for a forensics tool; Inter for body copy/forms keeps
dense UI legible. A deliberate pairing, not a default font stack.

### Signature element — the SHA-256 hash tag
`src/components/HashTag.jsx` renders a small monospace pill (`SHA256 a1b2c3d4…e9f0a1b2`,
click-to-copy) wherever evidence appears. This is the single recurring visual identity
element across the app, and it's tied to a real feature — the SHA-256 hashing already
computed by `TracerPipelineService` in Module 9 — not an arbitrary design flourish.

## Testing Strategy

Same layered philosophy as every prior module — separate pure logic from I/O, mock the
expensive/external parts:

```bash
npm test   # 29 tests
```

- `src/utils/format.test.js` — pure formatting functions (13 tests), zero dependencies
- `src/api/client.test.js` — API client with `fetch` mocked (6 tests) — never hits a real
  network or backend during tests
- `src/components/VerdictBadge.test.jsx` — component rendering (3 tests)
- `src/pages/Login.test.jsx` — real form validation logic (4 tests)
- `src/pages/Investigation.test.jsx` — full integration test: file upload → analyze → real
  result rendering, with `analyzeImage` mocked (3 tests) — verifies the actual user flow
  works correctly without needing the real backend or AI models running during tests

### A real testing-environment gap caught and fixed

`URL.createObjectURL` (a real, correctly-used browser API for image previews) isn't
implemented by jsdom, the DOM emulation library tests run against — this threw uncaught
errors during the Investigation page's file-upload tests. Fixed by mocking it in
`src/test-setup.js`, with an explicit comment distinguishing "test environment doesn't
implement this" from "the component has a bug" — worth being precise about that difference
in your report, since conflating the two would misdiagnose a correct component as broken.

## Local Setup

```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173`. The Investigation page needs the backend running (see
`backend/README.md`) — without it, analysis requests will show a clear "Could not reach the
TRACER backend" error rather than failing silently or confusingly.

## Completion Checklist

- [x] Login — real validation, honestly-scoped auth placeholder
- [x] Dashboard — real health check, clearly labeled placeholder stats
- [x] Investigation — fully real: upload, analyze, display verdict/heatmap/explanation/hash
- [x] Settings — real UI shell
- [x] Dark cybersecurity design system with a real, meaningful signature element
- [x] 29 tests passing, including a full mocked-API integration test
- [x] Production build verified (`npm run build` succeeds)
- [ ] Manually verify the Investigation page against your real running backend + trained
      detector (do this yourself — see "Local Setup" above)
