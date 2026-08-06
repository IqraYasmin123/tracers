# Module 14 — Report Generator

## Goal

Generate real, downloadable PDF and DOCX forensic reports for a case, pulling directly
from the same `Case`/`Evidence`/`AIResult` rows Module 13 already persists. No new AI
inference happens in this module — a report is a formatted export of data that was already
honestly computed (see Module 13's docs on why verdicts are always server-computed, never
client-reported). The `reports` table (Module 10) already existed for exactly this purpose.

## Scope

| Piece | What it does |
|---|---|
| `backend/app/services/report_service.py` | `generate_pdf_report()` (reportlab) and `generate_docx_report()` (python-docx) — real files, not stubs |
| `backend/app/api/routes/reports.py` | `POST /cases/{id}/reports`, `GET /cases/{id}/reports`, `GET /cases/{id}/reports/{id}/download` |
| `frontend/src/pages/CaseDetail.jsx` | "Generate PDF" / "Generate DOCX" buttons + a list of previously generated reports, each downloadable |

## A real gap found in Module 13, fixed here

While building this, I found that `AIResult.attribution_heatmap_path` — a column that's
existed in the schema since Module 10 — was never actually being populated.
`POST /cases/{id}/evidence` computed the heatmap PNG (via the same pipeline `/analyze`
uses) and returned it to the client, but discarded it afterward rather than saving it to
disk. A report that could only show the *numbers* around attribution (method, peak
fraction) but never the actual heatmap image would be a noticeably weaker report, so this
was fixed as groundwork for this module: the heatmap is now decoded and written to
`{evidence_storage_dir}/{case_id}/{uuid}_heatmap.png`, with the path stored on `AIResult`.
Verified by generating a real report and visually inspecting the rendered PDF — the
heatmap image is genuinely embedded, not just referenced.

## Report contents

Both formats contain the same information, laid out natively for their format (reportlab
`Table`/`Paragraph` flow for PDF, `Document`/heading styles for DOCX):

- Case number, title, status, description, created/generated timestamps
- A summary table: total evidence, clean count, adversarial count
- Per-evidence section, in upload order: filename, SHA-256 hash, upload time, verdict +
  confidence, attack type + confidence (if any), attribution method, the embedded heatmap
  image (if one was generated for that evidence), the explanation summary, and bullet
  details
- A disclaimer, present in every report, stating that verdicts come from an automated
  detector (citing Module 5's actual measured 86% accuracy / 0.95 AUC) and are not a
  substitute for expert human review — consistent with this project's stance throughout of
  never overstating what the model actually knows

## A design decision made explicitly

**Cases with zero evidence can still generate a report.** Rather than blocking report
generation until evidence exists, an empty case produces a valid (smaller) PDF/DOCX with
just the case info and summary table showing zero counts. This mirrors the project's
existing pattern of honest placeholders — a report for an empty case honestly says "0
evidence, 0 clean, 0 adversarial" rather than refusing to produce anything.

**Reports are immutable, point-in-time snapshots.** Generating a new report doesn't edit or
replace previous ones — every report a case has generated stays listed and downloadable,
each reflecting the case's evidence at the moment it was generated. There's no "regenerate"
or "delete report" action in this module; if that's needed later, it should be a deliberate,
distinct addition rather than something that silently makes past reports disappear.

## Import-order bug avoided proactively

Module 13 shipped with a real bug (see `docs/module13_case_management.md`) where
`database.models` was imported before `app.db` had patched `sys.path`, which passed every
`pytest` run but crashed real `uvicorn` immediately. Both new files here
(`app/api/routes/reports.py` and `app/schemas/reports.py`) apply the same fix proactively —
importing `app.db` (or `app`) first, purely for its `sys.path` side effect — and
`tests/test_fresh_import.py` (added in Module 13) continues to guard the whole app, not
just the routes that existed when it was written.

## Testing Strategy

```bash
cd backend && pytest -q     # 35 tests (25 pre-existing + 10 new)
cd frontend && npm test     # 99 tests (90 pre-existing + 9 new)
```

Backend report tests (`backend/tests/test_reports.py`) generate real files into pytest's
own `tmp_path` (see `conftest.py`'s `client` fixture, which now monkeypatches
`evidence_storage_dir`/`report_storage_dir` per test) — never the real `backend/data/`
directory. This also retroactively fixed a pre-existing hygiene gap: Module 13's tests had
been writing real evidence files into the working copy on every test run (harmless,
gitignored, but untidy); both fixtures are now isolated.

One test (`test_download_report_returns_the_real_file_bytes`) asserts the downloaded bytes
start with `%PDF` — checking the file is a genuine PDF, not just that the endpoint
returned `200`.

Beyond pytest, I manually generated a real PDF and DOCX outside the test suite, rendered
the PDF to an image with `pdftoppm`, and visually inspected it — confirming the summary
table, evidence section, embedded heatmap, and disclaimer all render correctly, not just
that the file has nonzero size.

## Local Setup

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```
Visit a case's detail page, click **+ Generate PDF** or **+ Generate DOCX**, then
**Download →** the resulting report from the list underneath.

## Completion Checklist

- [x] Real PDF generation (reportlab) with case info, summary stats, per-evidence detail,
      embedded heatmap, and a disclaimer
- [x] Real DOCX generation (python-docx) with equivalent content
- [x] `POST/GET /cases/{id}/reports` and a working download endpoint serving real file bytes
- [x] Fixed the Module 13 gap where attribution heatmaps were computed but never persisted
- [x] Frontend: generate + list + download UI on the Case Detail page
- [x] Proactively applied Module 13's import-order fix to the new files
- [x] 145 total tests passing (11 database + 35 backend + 99 frontend), zero regressions
- [x] Manually verified real generated output by rendering the PDF to an image and
      visually inspecting it
- [x] Production build verified (`npm run build` succeeds)
- [x] Generated report files excluded via `.gitignore`
