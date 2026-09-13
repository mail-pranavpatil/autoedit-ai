# AutoEdit AI — iOS shell

A thin native wrapper (Flutter `webview_flutter`) around the hosted AutoEdit
AI web app. All features come from the web app unchanged; this package only
adds the things a bare WebView can't do (Google OAuth, file downloads,
external links) and packages it as an installable iOS app.

Requires **macOS + Xcode + CocoaPods** to build locally. On Windows/Linux you
can still edit everything (`flutter analyze`/`flutter test` run anywhere) and
let CI compile it — `.github/workflows/ios.yml` runs the build on a
`macos-latest` runner on every push under `apps/mobile/**` (or via
**Actions → Build iOS → Run workflow**).

## Prerequisites

- Phase 0 done: the web app + API are live behind **one HTTPS origin** (Next.js
  serving the app and proxying `/api/*` + `/health` to FastAPI). The web build
  must run with `NEXT_PUBLIC_API_URL=""` (same-origin) and
  `API_PROXY_ORIGIN=<internal api url>`.
- Backend env: `COOKIE_SECURE=true`, `IOS_REDIRECT_SCHEME=autoedit`,
  `GOOGLE_REDIRECT_URI=https://<domain>/api/auth/callback`.
- Google Cloud console → the OAuth client → add redirect URIs:
  `https://<domain>/api/auth/callback` **and** `autoedit://auth/callback`.

## Configure for your deployment

One place to edit: `AUTOEDIT_APP_URL` (a `--dart-define`, see `lib/app_config.dart`
— the registrable domain used for cookie scoping and the "off-origin link"
check is derived from it, so there's nothing to keep in sync by hand).

```bash
flutter run --dart-define=AUTOEDIT_APP_URL=https://your-domain.example
```

## One-time setup (macOS)

```bash
cd apps/mobile
flutter pub get
```

## Xcode config (`ios/Runner/`)

- **Info.plist** already registers the `autoedit` custom scheme
  (`CFBundleURLTypes`) so the OAuth callback resolves, and sets
  `UIViewControllerBasedStatusBarAppearance = NO` /
  `UIStatusBarStyle = UIStatusBarStyleLightContent` (the web theme is
  dark-only).
- Bundle id `ai.autoedit.app` is already set on the Runner target.
- Signing & Capabilities → your personal team or an ad-hoc profile.
- App icon (1024²) + launch screen in `Assets.xcassets`.
- No ATS exceptions needed — all traffic is HTTPS to one host.
- No `NSCameraUsage*` / photo permissions — all media import is Google Drive
  inside the webview; downloads go through the share sheet.

## Build / run

```bash
flutter run --dart-define=AUTOEDIT_APP_URL=https://your-domain.example -d ios
open ios/Runner.xcworkspace   # to configure signing in Xcode
```

Distribute via **TestFlight** (internal testers, no App Store review) or export
a signed **ad-hoc IPA** (Product → Archive → Distribute App → Ad Hoc).

## CI

`.github/workflows/ios.yml` (`macos-latest`): `flutter pub get` → `flutter
analyze` → `flutter test` → `flutter build ios --no-codesign`. Green means the
shell compiles and its routing-logic tests pass; it uploads the unsigned
`Runner.app` as an artifact. It does **not** produce an installable IPA — that
needs Apple signing secrets + `xcodebuild -exportArchive`.

## How auth works in the shell

1. Web login button navigates to `/api/auth/google`.
2. `WebViewShell`'s navigation delegate (`lib/webview_shell.dart`,
   `classifyNavigation`) diverts that load (and the `accounts.google.com`
   consent screen) into `FlutterWebAuth2.authenticate(...)`, which opens
   `ASWebAuthenticationSession` on iOS at `/api/auth/google?platform=ios`.
3. Backend signs the platform into the OAuth `state`; after Google consent the
   callback (`services/api/routes/auth.py`) sees `platform=ios` and redirects
   to `autoedit://auth/callback?token=<session token>` instead of setting a
   cookie.
4. The shell pulls `token` out of the callback URL, writes it as the
   `autoedit_session` cookie via `WebViewCookieManager`, and reloads.
5. Session expiry (`api()` → `window.location = "/login"` → login button →
   `/api/auth/google`) re-enters step 2 automatically.

## What this package deliberately does NOT do

- **Push notifications** — the webview polls job status exactly like the
  browser. Add APNs + a device-token endpoint + a worker hook on
  `READY`/`FAILED` later if background awareness is needed.
- **Offline** — the shell loads the remote app; AutoEdit AI is useless offline
  anyway.
- **A native editor** — the CapCut-style editor runs as-is in the webview.
