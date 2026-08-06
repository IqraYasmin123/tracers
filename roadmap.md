# TRACER — Development Roadmap

Built strictly module-by-module. Each module must be complete, tested, and integrated before
the next one begins.

| # | Module | Tier | Status |
|---|---|---|---|
| 1 | Project Foundation & Environment Setup | Cross-cutting | ✅ Done |
| 2 | Vision-Language Model (VLM) Integration | AI engine | ✅ Done (incl. eager-attention fix, verified) |
| 3 | Dataset Management | AI engine | ✅ Done (14/14 tests passing) |
| 4 | Adversarial Attack Generation | AI engine | ✅ Done (11/11 tests, real PGD verified: 0.312→0.008 similarity) |
| 5 | Adversarial Detection Engine | AI engine | ✅ Done (12/12 tests; real results: binary 86% acc / 0.95 AUC, attack-type 74% acc) |
| 6 | Attention Analysis & Heatmap Generation | AI engine | ✅ Done (10/10 tests; real heatmaps verified — attention map showed new spurious hotspot under PGD attack) |
| 7 | Image Reconstruction | AI engine | ✅ Done (14/14 tests; real ablation: inpainting doesn't improve fidelity vs. no-reconstruction baseline for imperceptible attacks — architectural limitation, see docs) |
| 8 | Explainable AI (XAI) | AI engine | ✅ Done (20/20 tests, 0.34s; real capstone explanation generated and verified — **AI ENGINE COMPLETE** ) |
| 9 | FastAPI Backend | API layer | ✅ Done (8/8 tests, 0.07s — zero ML deps needed for tests) |
| 10 | Database Design | Data layer | ✅ Done (11/11 tests; Alembic migration verified end-to-end) |
| 11 | Desktop Dashboard (React) | Client layer | ✅ Done (29/29 tests; production build verified; Investigation page fully wired to real backend) |
| 12 | Analytics Dashboard | Client layer | ✅ Done (60/60 tests; live session stats + historical Module 5 metrics + honest placeholders; found & fixed missing SessionProvider mount / unwired Investigation recording — see docs/module12_analytics.md) |
| 13 | Case Management | API + Client | ✅ Done (25 backend + 29 new frontend tests, 90 total frontend; real cases/evidence CRUD wired to Module 10's schema; server always re-runs AI pipeline, never trusts client-reported verdicts; fixed a real import-order bug pytest missed but uvicorn caught — see docs/module13_case_management.md) |
| 14 | Report Generator | AI engine + API | ✅ Done (35 backend + 99 total frontend tests; real PDF/DOCX generation via reportlab + python-docx; fixed a Module 13 gap where attribution heatmaps were never persisted — see docs/module14_report_generator.md) |
| 15 | Mobile Application (Flutter) | Client layer | ⬜ Next |
| 16 | Security & Authentication | API layer | ⬜ |
| 17 | System Testing | Cross-cutting | ⬜ |
| 18 | Deployment & Documentation | Cross-cutting | ⬜ |

## Suggested Timeline (16 weeks)

| Weeks | Modules |
|---|---|
| 1 | Module 1 (Foundation) |
| 2–3 | Module 2–3 (VLM + Dataset) |
| 4 | Module 4 (Attacks) |
| 5 | Module 5 (Detection) |
| 6 | Module 6 (Attribution/Heatmaps) |
| 7 | Module 7 (Reconstruction) |
| 8 | Module 8 (XAI) |
| 9 | Module 9–10 (Backend + Database) |
| 10–11 | Module 11–12 (React Dashboard + Analytics) |
| 12 | Module 13–14 (Case Management + Reports) |
| 13 | Module 15 (Flutter Mobile) |
| 14 | Module 16 (Security) |
| 15 | Module 17 (Testing) |
| 16 | Module 18 (Deployment + final docs) |

## Module Completion Checklist

Each module is only marked ✅ once it has:
- [ ] Theory/architecture explanation documented
- [ ] Folder structure in place
- [ ] Working code, committed to Git
- [ ] Tests passing
- [ ] Integrated with previously completed modules
- [ ] Documentation updated (this roadmap + relevant `docs/` file)
