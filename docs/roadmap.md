# TRACER — Development Roadmap

Built strictly module-by-module. Each module must be complete, tested, and integrated before
the next one begins.

| # | Module | Tier | Status |
|---|---|---|---|
| 1 | Project Foundation & Environment Setup | Cross-cutting | ✅ Done |
| 2 | Vision-Language Model (VLM) Integration | AI engine | ✅ Done (incl. eager-attention fix, verified) |
| 3 | Dataset Management | AI engine | ✅ Done (14/14 tests passing) |
| 4 | Adversarial Attack Generation | AI engine | ⬜ Next |
| 5 | Adversarial Detection Engine | AI engine | ⬜ |
| 6 | Attention Analysis & Heatmap Generation | AI engine | ⬜ |
| 7 | Image Reconstruction | AI engine | ⬜ |
| 8 | Explainable AI (XAI) | AI engine | ⬜ |
| 9 | FastAPI Backend | API layer | ⬜ |
| 10 | Database Design | Data layer | ⬜ |
| 11 | Desktop Dashboard (React) | Client layer | ⬜ |
| 12 | Analytics Dashboard | Client layer | ⬜ |
| 13 | Case Management | API + Client | ⬜ |
| 14 | Report Generator | AI engine + API | ⬜ |
| 15 | Mobile Application (Flutter) | Client layer | ⬜ |
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
