# TRACER Frontend

React desktop dashboard — dark cybersecurity theme, real backend integration on the
Investigation page.

**Status:** Module 11 complete — Login (real validation), Dashboard (partial live data),
Investigation (fully wired to the Module 9 backend), Settings (UI shell). Case persistence
(Module 13) and analytics charts (Module 12) not yet wired in.

## Quick Start

```bash
npm install
npm run dev
```
Visit `http://localhost:5173`. Requires the backend (Module 9) running at
`http://127.0.0.1:8000` for the Investigation page to actually analyze images — see
`backend/README.md`.

## Testing

```bash
npm test
```
29 tests: pure utility functions, API client (mocked fetch), component rendering, and a full
Investigation-page integration test (upload → analyze → display results, with the API
mocked).

## Design System

- **Colors**: near-black charcoal base (`#0B0E14`), cyan accent (`#3DD6C4`), and three
  semantically-real verdict colors (clean/adversarial/warning) tied directly to actual
  detection states — see `tailwind.config.js`.
- **Type**: JetBrains Mono (data, verdicts, hashes) + Inter (body/forms).
- **Signature element**: the SHA-256 "chain of custody" hash tag (`src/components/HashTag.jsx`),
  shown wherever evidence appears — ties the real hashing feature from Module 9 into the
  visual identity throughout.

See [`docs/module11_frontend.md`](../docs/module11_frontend.md) at the repo root for full
design rationale.
