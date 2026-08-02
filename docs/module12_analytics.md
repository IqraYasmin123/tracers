# Module 12 — Analytics Dashboard

## Goal

Give the client layer a real analytics view without fabricating data Module 13 (Case
Management) hasn't been built to provide yet. Three honest, clearly-separated data sources:

1. **Live session data** — every real analysis run on the Investigation page is recorded
   client-side (`SessionContext`, backed by `localStorage`) and charted here: verdict
   counts, attack-type distribution, a confidence timeline, a threat gauge, average
   processing time, and a heatmap gallery. All computed from real usage, nothing invented.
2. **Historical evaluation metrics** — Binary Accuracy (86%), AUC (0.95), and Attack-Type
   Accuracy (74%) are the actual numbers from Module 5's offline evaluation run, shown
   under a "historical" label rather than presented as something computed live (arbitrary
   uploads have no ground truth, so a live accuracy figure would be meaningless).
3. **Honest placeholders** — Case Statistics (needs Module 13) and live Reconstruction
   Comparison (needs Module 9's deferred async job queue) are labeled as not-yet-available,
   same pattern used for Module 11's Dashboard placeholders.

## Scope, stated honestly

| Panel | Real functionality | Placeholder (arrives later) |
|---|---|---|
| Total/Clean/Adversarial/Avg. Confidence | Live, computed from `SessionContext` | — |
| Threat Gauge | Live, mean adversarial confidence over last 10 analyses | — |
| Confidence Timeline | Live, chronological | — |
| Attack Type Distribution | Live | — |
| Processing Time | Live average | — |
| Heatmap Gallery | Live, up to 12 most recent | — |
| Detector Model Performance | Real, but historical (Module 5's offline eval, not live) | — |
| Case Statistics | — | Module 13 |
| Live Reconstruction Comparison | — | Module 9 async job queue |

## A real integration bug found and fixed

The Analytics page, `analytics.js`, and their tests were already written and passing in
isolation before this session picked the module back up. Two integration gaps meant none
of it actually worked end-to-end in the real app, even though every test was green:

1. **`SessionProvider` was never mounted in `main.jsx`.** Every test that rendered
   `Analytics` or `Investigation` wrapped them in its own local `<SessionProvider>`, which
   masked the fact that the real app never did. Navigating to `/analytics` in a real
   browser would have thrown `useSession must be used within a SessionProvider` and
   crashed. Fixed by mounting `SessionProvider` once at the root in `main.jsx`, above
   `<App />`.
2. **`Investigation.jsx` never called `addAnalysis`.** The recording function existed on
   `SessionContext` and was unit-tested there, but nothing on the Investigation page
   actually called it after a successful analysis — so even with the provider mounted,
   Analytics would have stayed permanently empty. Fixed by calling `addAnalysis(analysis,
   { fileName: file.name })` in `handleAnalyze`'s success path, wrapped in a non-fatal
   try/catch so a storage failure never blocks the user from seeing their result.
3. **Routing/nav gap.** `/analytics` had no `<Route>` in `App.jsx` and no entry in
   `Sidebar.jsx`'s nav list, so the page was unreachable through the UI. Both added.
4. **Dashboard placeholder text was stale**, still describing Analytics as a future module
   after it existed. Updated to link to `/analytics` directly.

This is the kind of gap that a green test suite doesn't catch by itself, because
per-component tests each construct their own correct context. Added
`src/App.test.jsx` specifically to render full routes through the real `<App />` tree (the
same tree `main.jsx` mounts) so a missing provider or a missing route fails a test instead
of only failing in the browser.

## Design

`src/utils/analytics.js` is pure computation (no React, no charting library) over the
`sessions` array from `SessionContext` — same separation-of-concerns as the AI engine and
`utils/format.js`. Functions return `null` rather than `0` when there's no data yet
(e.g. `computeAvgConfidence`, `computeThreatLevel`), so the UI can render "—" / "NO DATA"
instead of a misleading zero that would read as "confirmed clean" or "confirmed safe".

Charts are hand-built SVG (`ThreatGauge`, `ConfidenceTimelineChart`, `AttackTypeBarChart`,
`HeatmapGallery`) rather than a charting library dependency, consistent with the project's
existing frontend footprint (no chart lib in `package.json`).

## Testing Strategy

```bash
npm test   # 60 tests
```

- `src/utils/analytics.test.js` — pure computation functions (16 tests), zero dependencies
- `src/pages/Analytics.test.jsx` — page-level rendering: live stats from seeded session
  data, historical metrics always shown, placeholders always shown (5 tests)
- `src/context/SessionContext.test.jsx` — recording, persistence, clearing (6 tests)
- `src/pages/Investigation.test.jsx` — extended with a test asserting a completed analysis
  is actually written to `localStorage` under `tracer.sessions.v1` (4 tests total)
- `src/App.test.jsx` — **new**: renders `/analytics`, `/dashboard`, `/investigation`
  through the real `App` + `SessionProvider` tree to catch the class of integration bug
  described above (3 tests)

## Local Setup

```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173/analytics`. Run at least one real analysis on `/investigation`
first — the live panels populate immediately after, no refresh needed, and persist across
reloads via `localStorage`.

## Completion Checklist

- [x] Live session stats (verdict counts, avg. confidence) computed from real Investigation
      analyses, not fabricated
- [x] Threat gauge, confidence timeline, attack-type distribution, processing time,
      heatmap gallery — all live
- [x] Historical detector metrics (Module 5) clearly labeled as historical, not live
- [x] Honest placeholders for Case Statistics (Module 13) and Reconstruction Comparison
      (Module 9 async queue)
- [x] `SessionProvider` mounted at the app root — live data actually flows in the real app,
      not just in tests
- [x] Investigation page records every completed analysis into session history
- [x] `/analytics` route and sidebar nav entry added
- [x] 60 tests passing, including a full-tree routing test that would catch a missing
      provider or missing route
- [x] Production build verified (`npm run build` succeeds)
