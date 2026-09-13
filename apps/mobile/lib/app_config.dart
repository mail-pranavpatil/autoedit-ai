/// Single-origin deployment this shell loads (Phase 0: Next.js serving the
/// web app + proxying /api/* and /health to FastAPI, both behind one host).
///
/// Override at build/run time: `flutter run --dart-define=AUTOEDIT_APP_URL=https://your-domain.example`
const String serverUrl = String.fromEnvironment(
  'AUTOEDIT_APP_URL',
  defaultValue: 'https://REPLACE-with-your-domain.example',
);

final Uri serverUri = Uri.parse(serverUrl);

/// Registrable domain of the deployment - derived from [serverUrl] so there is
/// only one place to edit (the old Capacitor shell needed this kept in sync by
/// hand in two files).
String get appHost => serverUri.host;

const String authScheme = 'autoedit';
const String sessionCookieName = 'autoedit_session';
