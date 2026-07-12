# TRACER — System Architecture

## Overview

TRACER is a three-tier system:

```
Client layer        React web dashboard  |  Flutter mobile app
                              |  REST API calls
API layer            FastAPI backend (auth, routing, business logic)
                              |  DB + inference calls
Data & AI layer      AI engine (PyTorch, CLIP)  |  PostgreSQL database
```

## Tier Responsibilities

### Client layer (React + Flutter)
- Never talks to the AI engine or database directly.
- Only communicates with the backend over authenticated REST endpoints.
- Owns presentation only: rendering results, charts, forms. No business logic, no AI logic.

### API layer (FastAPI)
- Single entry point for all clients.
- Owns: authentication/authorization (JWT), request validation, case/report business logic,
  calling the AI engine, persisting results to PostgreSQL, audit logging.
- Never trains or fine-tunes models — it calls the AI engine's inference functions and stores
  the results.

### Data & AI layer
- **AI engine**: a frozen, pretrained CLIP backbone plus TRACER's own detection, attribution,
  and reconstruction logic (Modules 2–8). Exposed to the backend as plain Python function calls
  (imported as a package) — not a separate network service, to avoid unnecessary latency and
  deployment complexity for an FYP-scale system.
- **PostgreSQL**: system of record for users, cases, evidence, AI results, reports, and audit
  logs. See `database/schemas/` for the full ER diagram (Module 10).

## Why This Separation Matters (for your viva)

A common FYP failure mode is a single monolithic script that mixes model inference, business
rules, and UI rendering. TRACER instead follows standard SE separation of concerns:

- **Testability**: the AI engine can be unit-tested with plain Python/pytest, independent of
  any running server or browser.
- **Replaceability**: CLIP could be swapped for another VLM without touching the backend,
  frontend, or database schema — only `ai-engine/src/vlm/` changes.
- **Security boundary**: the AI engine never sees a client request directly; everything passes
  through the backend's auth and validation layer first.

## Why CLIP, Not a Unified/Fused VLM

See the root `README.md` for the full rationale. In short: CLIP's dual-encoder design keeps the
vision transformer's attention inspectable in isolation from the text branch, which is a
requirement for the detection (Module 5) and attribution (Module 6) modules. A fused
cross-attention model would blur that boundary.

## Module → Tier Mapping

| Module | Tier |
|---|---|
| 1. Project Foundation | — (cross-cutting) |
| 2. VLM Integration | AI engine |
| 3. Dataset Management | AI engine |
| 4. Adversarial Attack Generation | AI engine |
| 5. Detection Engine | AI engine |
| 6. Attention & Heatmaps | AI engine |
| 7. Image Reconstruction | AI engine |
| 8. Explainable AI | AI engine |
| 9. FastAPI Backend | API layer |
| 10. Database Design | Data layer |
| 11. React Dashboard | Client layer |
| 12. Analytics Dashboard | Client layer (+ backend endpoints) |
| 13. Case Management | API + Client layer |
| 14. Report Generator | AI engine (PDF gen) + API layer |
| 15. Flutter Mobile App | Client layer |
| 16. Security & Auth | API layer (cross-cutting) |
| 17. System Testing | Cross-cutting |
| 18. Deployment & Docs | Cross-cutting |
