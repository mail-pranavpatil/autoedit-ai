# AutoEdit AI — iOS shell

A thin native wrapper (Capacitor / WKWebView) around the hosted AutoEdit AI web
app. All features come from the web app unchanged; this package only adds the
things a bare WebView can't do (Google OAuth, file downloads, external links,
safe-area layout) and packages it as an installable iOS app.

Requires **macOS + Xcode + CocoaPods** to build locally. On Windows/Linux you can
still edit everything and let CI compile it — `.github/workflows/ios.yml` runs the
build on a `macos-latest` runner on every push under `apps/mobile/**` (or via
**Actions → Build iOS → Run workflow**).

The native glue lives in `local-plugins/autoedit-native/` as a local Capacitor
plugin. `npx cap sync ios` links it through CocoaPods automatically — there is no
"add the file to the Xcode target" step.

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

Edit two constants so they match your single-origin domain:

- `capacitor.config.js` → `SERVER_URL` (or set the `AUTOEDIT_APP_URL` env var at
  build time).
- `local-plugins/autoedit-native/ios/Sources/AutoeditNativePlugin/AutoEditNativePlugin.swift`
  → `appHost` (registrable domain, no scheme).

## One-time setup (macOS)

```bash
cd apps/mobile
npm ci                   # resolves the local autoedit-native plugin
npx cap add ios          # generates ios/ (git-ignored)
npx cap sync ios         # copies web assets + links the plugin pod
```

## Xcode config (`ios/App/App/`)

- **Info.plist** → register the custom scheme so the OAuth callback and deep
  links resolve:
  ```xml
  <key>CFBundleURLTypes</key>
  <array>
    <dict>
      <key>CFBundleURLSchemes</key>
      <array><string>autoedit</string></array>
    </dict>
  </array>
  ```
- **Info.plist** → `UIViewControllerBasedStatusBarAppearance = NO`,
  `UIStatusBarStyle = UIStatusBarStyleLightContent` (the web theme is dark-only).
- Signing & Capabilities → your personal team or an ad-hoc profile. Bundle id
  `ai.autoedit.app`.
- App icon (1024²) + launch screen in `Assets.xcassets`.
- No ATS exceptions needed — all traffic is HTTPS to one host.
- No `NSCameraUsage*` / photo permissions — all media import is Google Drive
  inside the webview; downloads go through the share sheet.

## Build / run

```bash
npm run sync      # cap sync ios  (after any config or glue change)
npm run open      # opens ios/App/App.xcworkspace in Xcode
npm run run       # cap run ios   (simulator / attached device)
```

Distribute via **TestFlight** (internal testers, no App Store review) or export a
signed **ad-hoc IPA** (Product → Archive → Distribute App → Ad Hoc).

## CI

`.github/workflows/ios.yml` (`macos-latest`): `npm ci` → `npx cap add ios` →
`npx cap sync ios` → `pod install` → unsigned `xcodebuild`. Green means the shell
and the `autoedit-native` Swift compile; it uploads the unsigned `App.app` as an
artifact. It does **not** produce an installable IPA — that needs Apple signing
secrets (`APPLE_CERT_P12_BASE64`, `APPLE_CERT_PASSWORD`,
`APPLE_PROVISIONING_PROFILE_BASE64`) + `xcodebuild -exportArchive`.

## How auth works in the shell

1. Web login button navigates to `/api/auth/google`.
2. `AutoEditNativePlugin.shouldOverrideLoad` cancels that load and opens
   `ASWebAuthenticationSession` at `/api/auth/google?platform=ios`.
3. Backend signs the platform into the OAuth `state`; after Google consent the
   callback (`services/api/routes/auth.py`) sees `platform=ios` and redirects to
   `autoedit://auth/callback?token=<session token>` instead of setting a cookie.
4. The plugin pulls `token` out of the callback URL, writes it as the
   `autoedit_session` cookie into the WebView's cookie store, and reloads.
5. Session expiry (`api()` → `window.location = "/login"` → login button →
   `/api/auth/google`) re-enters step 2 automatically.

## What this package deliberately does NOT do

- **Push notifications** — the webview polls job status exactly like the browser.
  Add APNs + a device-token endpoint + a worker hook on `READY`/`FAILED` later if
  background awareness is needed.
- **Offline** — `server.url` loads the remote app; AutoEdit AI is useless offline
  anyway.
- **A native editor** — the CapCut-style editor runs as-is in the webview.
