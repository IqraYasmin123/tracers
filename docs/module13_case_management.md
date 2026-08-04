# Module 13 — Case Management

## Goal

Wire Module 10's already-designed `cases` / `evidence` / `ai_results` schema into a real
API and UI: create and track forensic cases, attach real AI analyses to them (re-run
server-side, never trusted from the client), and browse the results. No schema changes
were needed — Module 10 was built with this module in mind (`database/connection.py`'s
`get_db()` was already documented as "not yet wired in — that happens in Module 13").

## Scope

| Piece | What it does |
|---|---|
| `backend/app/db.py` | Wires `database/connection.py`'s `get_db()` into the FastAPI app, the same pattern `pipeline_service.py` used for `ai-engine/src` |
| `backend/app/services/system_user.py` | Temporary attribution stand-in until Module 16 (auth) exists — see below |
| `backend/app/api/routes/cases.py` | `POST/GET /cases`, `GET/PATCH /cases/{id}`, `POST /cases/{id}/evidence`, `GET /cases/stats` |
| `frontend/src/pages/Cases.jsx` | List, filter by status, create a case |
| `frontend/src/pages/CaseDetail.jsx` | Case info, status editing, evidence list with AI verdicts |
| Investigation page | New "Save to Case" panel — attaches the just-analyzed image to an existing or new case |
| Analytics page | "Case Statistics" placeholder is now real, live data (was `Arrives with Module 13`) |
| Dashboard page | All four summary stat cards are now real, live data (were all placeholders) |

## Two real design decisions, made explicitly rather than glossed over

**1. No real user/auth yet.** `Case.created_by` and `Evidence.uploaded_by` are required,
non-nullable foreign keys to `users.id` — deliberately not nullable, because a forensic
system should never allow an unattributed case or piece of evidence, even temporarily.
Module 16 (Security & Authentication) doesn't exist yet, so there's no real login to
attribute to. Rather than weaken the schema to work around a temporary gap,
`app/services/system_user.py` seeds one placeholder `system` user and attributes every
case/evidence row to it until Module 16 lands. Its `password_hash` is a fixed sentinel
string, not a real hash of anything, and the file documents explicitly that this account
must never be reachable through a real login endpoint — whoever builds Module 16 needs to
either exclude `username == "system"` from login or replace every caller of
`get_or_create_system_user()` with real current-user resolution.

**2. The AI verdict is always computed server-side, never accepted from the client.**
`POST /cases/{id}/evidence` takes a raw image upload and runs the *real* pipeline
(`TracerPipelineService.analyze()`) inside the request — the same function `/analyze`
uses — rather than accepting a JSON body of "here's the result, please save it." A
forensic case record that trusted client-reported verdicts could be tampered with by
anyone sending a crafted request; re-running detection server-side means the case's
evidence trail is only ever as trustworthy as the model itself, not the client.

## What's honestly still missing

- **Real authentication** — the system-user placeholder above is a known, documented gap,
  not a finished feature. Anyone with API access can currently create/modify any case.
- **Evidence file cleanup** — `POST /cases/{id}/evidence` writes the uploaded image to
  `backend/data/evidence/{case_id}/{uuid}{ext}` and never deletes it, even if the case is
  later deleted. There's no case-delete endpoint yet (see below), so this hasn't mattered
  in practice, but it will need addressing before this handles real storage limits.
- **No hard case delete.** Only `status` can move to `archived` — deliberate, since
  `Case.evidence` cascades on delete (see `database/models.py`), and forensic case data
  shouldn't be silently destroyable. If a real "delete" is ever needed, it should be a
  distinct, audited, permission-gated action in a later module, not added here casually.
- **Report generation** (Module 14) still needs building — `reports` table exists in the
  schema but nothing writes to it yet.

## Testing Strategy

```bash
cd backend && pytest -q     # 24 tests (8 pre-existing + 16 new)
cd frontend && npm test     # 90 tests (61 pre-existing + 29 new)
```

Backend tests (`backend/tests/test_cases.py`) use a fresh in-memory SQLite database per
test (`StaticPool` keeps it alive across the multiple `get_db()` calls one request can
trigger) plus the existing `FakePipelineService`/`FailingPipelineService` pattern from
Module 9 — no real AI models, no shared state between tests. Covers: case CRUD, status
filtering, 404s, evidence attachment (including the pipeline-not-ready 503 case), and the
stats endpoint's aggregation logic.

Frontend tests cover the new API client functions (`src/api/client.test.js`), the new
formatting helpers (`src/utils/format.test.js`), both new pages
(`Cases.test.jsx`, `CaseDetail.test.jsx`), the Investigation page's new Save-to-Case flow
(existing-case path, create-new-case path, and the validation-error path), and an
`App.test.jsx` regression test rendering the real `/cases/:caseId` route through the full
`App` + `SessionProvider` tree — the same pattern that caught Module 12's missing-provider
bug, now guarding this module's routes too.

## Local Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload   # creates tracer_dev.db automatically on first run
```
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173/cases`. Create a case, then go to Investigation, run a real
analysis, and use the new "Save to Case →" panel to attach it — it should immediately
appear on the case's detail page, and the case statistics on Analytics/Dashboard should
update on next load.

## Completion Checklist

- [x] `cases`/`evidence`/`ai_results` tables (Module 10) wired into the FastAPI backend
- [x] Full case CRUD: create, list (with status filter), detail, partial update
- [x] Evidence attachment re-runs the real AI pipeline server-side, never trusts the client
- [x] Case statistics endpoint backs both Analytics' "Case Statistics" panel and
      Dashboard's summary cards — closing placeholders from Modules 11 and 12
- [x] Temporary system-user attribution documented as temporary, with an explicit note for
      whoever builds Module 16
- [x] 24/24 backend tests, 90/90 frontend tests, zero regressions across database/backend/
      frontend tiers
- [x] Production build verified (`npm run build` succeeds)
- [x] Evidence files and the dev SQLite database excluded via `.gitignore`
