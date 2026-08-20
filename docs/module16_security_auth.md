# Module 16 — Security & Authentication

## Goal

Replace Module 13's temporary "system user" placeholder with real authentication: password
hashing, JWT-issued sessions, role-based access control, and finally activating the
`AuditLog` table that's existed unused in the schema since Module 10. Every case, evidence
upload, and report generated from here on is attributed to a real, authenticated person —
not a shared placeholder account.

## Two decisions made explicitly, per instruction to follow standard security practice

**1. Admin-provisioned accounts only — no public self-registration.** A forensic system
that handles evidence should not have an open sign-up form. The first admin account is
created once, automatically, the first time the app starts against an empty `users` table
— with a **randomly generated password printed to the console exactly once** (see
`app/auth/bootstrap.py`), the same pattern Django's `createsuperuser` and Jenkins' initial
admin password file use. It is never hardcoded, never stored in config, and never
committed. Every account after that is created by an existing admin via
`POST /auth/users`.

**2. Real role-based access control**, not just "logged in or not":
- **VIEWER** — read-only: can list/view cases, evidence, and reports
- **INVESTIGATOR** — VIEWER's permissions, plus create/update cases, attach evidence, generate reports
- **ADMIN** — INVESTIGATOR's permissions, plus create other user accounts

## Scope

| Piece | What it does |
|---|---|
| `backend/app/auth/security.py` | bcrypt password hashing (constant-time verify), JWT issuance/decoding |
| `backend/app/auth/dependencies.py` | `get_current_user`, `require_role()` factory, and convenience `require_viewer_or_above`/`require_investigator_or_above`/`require_admin` |
| `backend/app/auth/bootstrap.py` | One-time initial-admin creation, described above |
| `backend/app/auth/audit.py` | Writes real rows to `audit_logs` — finally used, not just modeled |
| `backend/app/auth/routes.py` | `POST /auth/login`, `GET /auth/me`, `POST /auth/users` (admin-only), `PATCH /auth/me/password` |
| `cases.py` / `reports.py` | Every route now requires authentication; mutations require investigator role or above |
| `frontend/src/context/AuthContext.jsx` | React-facing auth state; validates stored tokens against `/auth/me` rather than trusting `localStorage` blindly |
| `frontend/src/components/RequireAuth.jsx` | Route guard — redirects to `/login`, preserving the originally-requested page |
| `frontend/src/pages/Login.jsx` | Real login, not the old client-side-only placeholder |
| `mobile/lib/api/client.dart`, `login_screen.dart`, `main.dart`, `settings_screen.dart` | Same real auth flow for the Flutter app: login, startup session check, logout |

## What "generic error message" security choices were made, and why

`POST /auth/login` returns the exact same `401 Incorrect username or password.` whether the
username doesn't exist or the password is wrong — a different message for each would let an
attacker enumerate which usernames are real accounts. `get_current_user` does the same
thing when a token references a since-deleted account: it's treated identically to an
invalid token (a generic 401), not a distinguishable error, for the same reason.

## Real bugs found and fixed while reviewing this module

**1. The exact import-order bug from Module 13, again, in two new files.**
`app/auth/bootstrap.py` and `app/auth/audit.py` both imported `database.models` directly,
without the `from .. import db as _db` sys.path-priming guard that every other backend
file learned to include after your real uvicorn crash in Module 13. They "worked" only
because `main.py` happens to import `cases.py` (which does prime the path) before either
of them — the exact same fragile, lucky ordering that broke before. Fixed both
defensively, and reconfirmed with the fresh-process import check
(`tests/test_fresh_import.py`) that this doesn't regress.

**2. A live regression in the React frontend: report downloads were broken.**
Module 14's `CaseDetail.jsx` used a plain `<a href>` to download reports. Module 16 adds
required authentication to the download endpoint — but a browser's plain link navigation
cannot carry a custom `Authorization` header. `client.js` had already been updated with a
proper `downloadReport()` (fetch with the auth header, then trigger a blob save), but
`CaseDetail.jsx` was still calling a function (`getReportDownloadUrl`) that no longer
existed — this would have thrown at runtime the moment someone clicked Download. Fixed by
wiring the component to the real `downloadReport()` function with a button instead of a
bare link, with proper loading/error states.

**3. The same download problem in the mobile app, for the same reason** — `url_launcher`
opening a bare URL externally can't carry an auth header either. Fixed using
`downloadReportBytes()` (an authenticated fetch) plus `share_plus` to hand the bytes to the
OS's native share/save sheet, avoiding the need for raw file-system write permissions.

**4. Mobile's Login screen and startup flow were never actually wired to the real auth
API**, even though `ApiClient` already fully supported it. `LoginScreen` still just faked a
delay and navigated to the dashboard; `main.dart` unconditionally started at the login
screen regardless of whether a valid session existed. Fixed: `LoginScreen` now takes the
`ApiClient` and calls the real `login()`, surfacing real backend error messages; `main.dart`
now checks `getCurrentUserOrNull()` (which validates the stored token against `/auth/me`,
mirroring `AuthContext.jsx`'s own behavior) to decide the real starting route. Added a
logout button to the Settings screen, which didn't exist anywhere before.

## Known limitations, stated honestly

- **No token refresh flow.** Access tokens last 8 hours (`ACCESS_TOKEN_EXPIRE_MINUTES`);
  after that, re-login is required. A refresh-token rotation flow is real additional scope
  deliberately left out of this pass.
- **No mid-session 401 handling in the UI.** If a token expires or is revoked while someone
  is actively using the app, the next request fails with a generic error message rather
  than an automatic redirect back to login. Both React's `RequireAuth` and the mobile
  bootstrap check correctly gate initial page loads — this gap is specifically about
  requests that happen *after* a page has already rendered.
- **No rate limiting on login attempts.** Failed logins are audit-logged (so the data to
  detect brute-forcing exists), but nothing currently blocks repeated attempts. Real rate
  limiting needs shared state (e.g. Redis) that doesn't exist in this project yet.
- **CORS is a real allowlist now** (`ALLOWED_ORIGINS`, defaulting to the React dev server),
  replacing Module 9's original wildcard — but Flutter Web's dev server picks a random port
  on every run, so local mobile-web testing needs either `flutter run -d chrome
  --web-port=<fixed-port>` with that port added to `ALLOWED_ORIGINS`, or a temporarily
  looser value for local development only.

## Testing Strategy

```bash
cd backend && pytest -q     # 54 tests (all pre-existing + 19 new: 14 auth + 5 bootstrap)
cd frontend && npm test     # 109 tests (all pre-existing + 10 new: 5 Login rewritten + auth/download coverage)
```

Backend auth tests (`test_auth.py`) cover: login success (by username and by email), wrong
password and nonexistent username both returning the same generic message, missing-token
401s, role enforcement in both directions (viewer blocked from mutating, investigator
allowed), admin-only user creation and its duplicate-detection, and self-service password
change requiring the current password. `test_bootstrap.py` covers: admin creation on an
empty table, doing nothing when accounts already exist, the printed password actually
matching what got hashed and stored, and that generated passwords aren't predictable.

Frontend tests wrap every page that renders `Sidebar`/`Topbar` (which call `useAuth()`) in
a real `AuthProvider`, rather than mocking the hook away — so these tests exercise the
actual context logic, not a stand-in for it. `App.test.jsx` gained a real regression test
confirming `RequireAuth` actually redirects to `/login` when no token is stored, not just
that it exists in the tree.

Mobile has no automated tests for this module, for the same reason stated in
`docs/module15_mobile.md`: no Flutter tooling is available in this environment to run them.

## Completion Checklist

- [x] bcrypt password hashing, JWT issuance/validation
- [x] Role-based access control enforced on every case/report route
- [x] One-time randomly-generated initial admin, no hardcoded default credentials
- [x] Audit logging active (`AuditLog` table, unused since Module 10, now written to)
- [x] React: real login, route guards, logout, and a fixed download regression
- [x] Mobile: real login, startup session check, logout, and a fixed download regression
- [x] Proactively re-applied the Module 13 import-order fix to two new files
- [x] 54 backend + 109 frontend tests passing, zero regressions
- [x] Production build verified (`npm run build` succeeds)
- [x] Known limitations (token refresh, mid-session 401s, rate limiting) stated explicitly
      rather than silently left out
