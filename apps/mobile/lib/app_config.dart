/// Single-origin deployment this shell loads (Phase 0: Next.js serving the
/// web app + proxying /api/* and /health to FastAPI, both behind one host).
///
/// Override at build/run time: `flutter run --dart-define=AUTOEDIT_APP_URL=https://your-domain.example`
const String serverUrl = String.fromEnvironment(
  'AUTOEDIT_APP_URL',
  defaultValue: 'https://autoedit-web.onrender.com',
);

final Uri serverUri = Uri.parse(serverUrl);

/// Registrable domain of the deployment - derived from [serverUrl] so there is
/// only one place to edit (the old Capacitor shell needed this kept in sync by
/// hand in two files).
String get appHost => serverUri.host;

const String authScheme = 'autoedit';
// Must match the cookie name apps/web mirrors its Supabase session into
// (components/providers.tsx) and that get_current_user reads as a fallback.
const String sessionCookieName = 'sb_access_token';

/// Supabase: system of record for login/signup. The anon key is a public,
/// client-safe key by design (Supabase's own recommendation is to embed it
/// directly in client apps) - only SUPABASE_JWT_SECRET on the backend is
/// actually secret.
const String supabaseUrl = String.fromEnvironment(
  'SUPABASE_URL',
  defaultValue: 'https://gxwungthmfdbtjnbbupm.supabase.co',
);
const String supabaseAnonKey = String.fromEnvironment(
  'SUPABASE_ANON_KEY',
  defaultValue:
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd4d3VuZ3RobWZkYnRqbmJidXBtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkzOTM5NjksImV4cCI6MjEwNDk2OTk2OX0.WCsC1bAfd5aMKz7nmAfgR__hbMk7uFONBbQeaKZm6EI',
);
