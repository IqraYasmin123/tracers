# Module 15 — Mobile Application (Flutter)

## An important honesty note before anything else

**Every previous module in this project was verified by actually running its tests and
builds** — pytest, vitest, `npm run build`, even a fresh-process import check for the
uvicorn bug. This module is different: **I do not have Flutter/Dart tooling available in
my environment** (network access is restricted to package registries like pypi/npm/GitHub,
not Flutter's SDK distribution). I cannot run `flutter pub get`, `flutter analyze`,
`flutter test`, or `flutter build` myself.

That means, unlike Modules 9-14, I cannot claim "N tests passing" here, because none have
been run. The code below was written carefully, mirroring the real, already-verified React
frontend and FastAPI backend contracts field-for-field — but it has not been compiled. You
should expect to hit at least a few real compile errors on first run, and that's expected,
not a sign the approach is wrong. Report them back the same way you did for the backend
import-order bug, and we'll fix them together.

## Scope

| Screen | What it does |
|---|---|
| Login | Client-side form validation only — mirrors `frontend/src/pages/Login.jsx`'s honest placeholder exactly. No real backend auth call, because Module 16 doesn't exist yet. |
| Dashboard | Real case statistics from `GET /api/v1/cases/stats` (Module 13/14's endpoint) |
| Investigation | Camera capture or gallery pick → `POST /api/v1/analyze` → real verdict, heatmap, explanation. "Save to Case" reuses `POST /cases/{id}/evidence`. |
| Cases | List/filter/create — same endpoints as `frontend/src/pages/Cases.jsx` |
| Case Detail | Status editing, evidence list, report generation (PDF/DOCX) and download |
| Settings | Configurable backend URL (see "Connecting to your backend" below) + connection test |

## Two scope decisions made explicitly

**Notifications are local-only, not push.** The mobile README's original scope listed
"notifications," but there is no push infrastructure anywhere in this system — no FCM
device-token registration, no notification records in `database/models.py`. Rather than
build something that looks like push notifications but silently does nothing server-side,
`lib/notifications/notification_service.dart` fires a **local** notification from the same
device, at the moment an action finishes on that device (e.g. "Analysis complete" after
`/analyze` returns). This is an honest, real feature — useful if the app is backgrounded
during a slow analysis — without pretending server-side infrastructure exists.

**Login stays a placeholder, matching React exactly.** Real JWT authentication arrives in
Module 16. Building a fake "always succeeds" login here would be more misleading than
being direct about what's implemented, so this mirrors `Login.jsx`'s own approach and its
own comment explaining why.

## A real bug found after you tested it, and fixed

Testing on Chrome (`flutter run -d chrome`) surfaced a real platform bug: the Investigation
screen originally used `dart:io.File` and `Image.file`/`http.MultipartFile.fromPath` to
handle picked images — none of which work on Flutter Web, since a browser has no real
filesystem to point a `File` at. This crashed with `Image.file is not supported on Flutter
Web` the moment an image was picked.

Fixed by switching to a bytes-based approach everywhere: `image_picker`'s `XFile.readAsBytes()`
instead of wrapping the path in a `File`, `Image.memory` instead of `Image.file` for
preview, and `http.MultipartFile.fromBytes` instead of `.fromPath` for uploads — all of
which work identically on web, Android, and iOS. This also caught a second, related issue:
`MultipartFile.fromBytes` defaults to `application/octet-stream` unless given an explicit
content type, which the backend's allowlist (`image/jpeg`/`png`/`webp` — see
`backend/app/api/routes/inference.py` and `cases.py`) would have rejected with a 422. Fixed
by inferring the real content type from the filename extension (`http_parser`'s
`MediaType`) before upload.

## Required setup steps (do these first)

The `mobile/` folder as delivered has `lib/`, `pubspec.yaml`, and this doc — but **not**
the native `android/`, `ios/`, etc. platform folders, because generating those by hand
(rather than with Flutter's own tooling) would be far more likely to be subtly broken than
useful. Generate them with Flutter itself:

```bash
cd mobile
flutter create --org com.tracer .
```

This is safe to run even though `lib/` and `pubspec.yaml` already exist — `flutter create`
does not overwrite existing files by default, it only fills in what's missing (the
`android/`, `ios/`, `web/`, etc. folders and their boilerplate).

Then:

```bash
flutter pub get
```

### Required manual permission additions

`flutter create` won't know this app needs camera and internet access — add these
yourself after running it:

**`android/app/src/main/AndroidManifest.xml`** — inside the `<manifest>` tag, alongside
`<application>`:
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.CAMERA" />
```

**`ios/Runner/Info.plist`** — inside the outermost `<dict>`:
```xml
<key>NSCameraUsageDescription</key>
<string>TRACER needs camera access to capture evidence images for analysis.</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>TRACER needs photo library access to select evidence images for analysis.</string>
```

## Connecting to your backend

The default backend URL (`http://10.0.2.2:8000`) only works for the **Android emulator**,
where `10.0.2.2` is a special alias for your computer's own `localhost`. For anything else:

- **iOS simulator**: use `http://127.0.0.1:8000` (the simulator shares your Mac's network stack directly)
- **A physical phone**: your phone and computer must be on the same Wi-Fi network. Find your
  computer's LAN IP (Windows: `ipconfig`, look for IPv4 Address) and use
  `http://<that-ip>:8000` — e.g. `http://192.168.1.42:8000`. You'll also need to make sure
  `uvicorn` is bound to `0.0.0.0`, not just `127.0.0.1` (add `--host 0.0.0.0` to the
  `uvicorn app.main:app --reload` command), or your phone won't be able to reach it at all.

Change this any time from the app's **Settings** tab — it's saved locally via
`shared_preferences`, no rebuild needed.

## What I could and couldn't verify

**Could verify (by reading, not running):**
- Every API call's URL, method, and request/response field names against the actual
  backend route files (`backend/app/api/routes/*.py`) and schemas — these should be
  correct, since I copied field names directly rather than reconstructing them from memory
- The color values match `frontend/tailwind.config.js` exactly

**Could not verify:**
- That any of this actually compiles
- That `image_picker`, `flutter_local_notifications`, or `url_launcher` are configured
  correctly for your specific Flutter/Android/iOS SDK versions — these packages
  occasionally have version-specific native setup steps beyond what's in this doc
- Any actual UI behavior on a real device or emulator
- Widget tests — I deliberately did not write any. A test I can't run and iterate on
  myself is worse than no test: it would give false confidence rather than real coverage.
  Once you have this running, ask me to add tests and I'll write them against what's
  actually confirmed working.

## Local Setup (after the required setup steps above)

```bash
cd mobile
flutter pub get
flutter run
```

Then walk through: Login (any valid-looking email/8+ char password) → Dashboard (should
show real numbers if your backend has cases) → Investigation (pick or capture an image,
analyze, save to a case) → Cases (see it listed) → tap into the case → generate a report →
download it.

## Completion Checklist

- [x] All screens written against the real, already-verified backend API contract
- [x] Field names cross-checked against `backend/app/schemas/*.py`, not reconstructed from memory
- [x] Honest scope decisions documented (local-only notifications, placeholder login)
- [ ] **Not yet verified**: compiles, runs, passes any test — needs your local Flutter environment
- [ ] Native platform folders (`android/`, `ios/`) — generate with `flutter create .`, not included here
- [ ] Widget tests — deliberately deferred until the app is confirmed running
