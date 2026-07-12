# TRACER
### Transformer-based Digital Forensics Framework for Detecting and Reconstructing Adversarial Attacks in Vision-Language Models

TRACER is a full-stack digital forensics platform for Vision-Language Models (VLMs). It
passively detects adversarial manipulation of image-text inputs, localizes the manipulated
region via gradient-based attribution, reconstructs a clean version of the input via guided
diffusion, and packages every step into a court-ready-style forensic report — all without
requiring watermarking or access to the original attack process.

This repository is organized as a **monorepo** with clearly separated tiers so the AI research
code, backend, frontend, and mobile app can be developed, tested, and deployed independently.

## System Architecture

```
Client layer        React web dashboard  |  Flutter mobile app
                              |  REST API calls
API layer            FastAPI backend (auth, routing, business logic)
                              |  DB + inference calls
Data & AI layer      AI engine (PyTorch, CLIP)  |  PostgreSQL database
```

## Repository Structure

```
TRACER/
├── ai-engine/       AI research + inference code (Python, PyTorch, Colab notebooks)
├── backend/         FastAPI REST API, business logic, auth
├── frontend/        React desktop dashboard (dark cybersecurity theme)
├── mobile/          Flutter mobile app
├── database/        PostgreSQL schema, ER diagrams, migrations
├── docs/            Architecture docs, API docs, setup guides, roadmap
├── scripts/         Setup/dev automation scripts
└── .github/         CI workflows
```

Each subfolder has its own README with tier-specific setup instructions.

## Why CLIP (not a unified/fused VLM)

TRACER deliberately builds on CLIP's **dual-encoder** design: a vision transformer and a text
transformer whose outputs are only compared via cosine similarity — never fused into one shared
attention stack. That separation is exactly what makes CLIP's vision-encoder attention
inspectable in isolation, which is what the detection and attribution modules rely on. A fused
multimodal model (cross-attention between image and text tokens inside one stack, e.g. BLIP-2,
LLaVA) would blur the exact boundary TRACER is designed to forensically probe. Cross-architecture
comparison against a fused model is listed as a future-work extension, not a core requirement.

## Development Status

Built module-by-module per the project roadmap — see [`docs/roadmap.md`](docs/roadmap.md) for
the full 18-module plan and current progress.

**Current module:** Module 1 — Project Foundation & Environment Setup ✅

## License

MIT — see [LICENSE](LICENSE).
